from __future__ import annotations

import datetime
import logging
import os
from typing import TYPE_CHECKING, Any

import boto3
from aws_lambda_powertools.shared import constants, user_agent
from aws_lambda_powertools.utilities.idempotency import BasePersistenceLayer
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyItemAlreadyExistsError,
    IdempotencyItemNotFoundError,
    IdempotencyValidationError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.datarecord import (
    STATUS_CONSTANTS,
    DataRecord,
)
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from botocore.config import Config
    from mypy_boto3_dynamodb.client import DynamoDBClient
    from mypy_boto3_dynamodb.type_defs import AttributeValueTypeDef

logger = logging.getLogger(__name__)


class DynamoDBPersistenceLayer(BasePersistenceLayer):
    def __init__(
        self,
        table_name: str,
        key_attr: str = "id",
        static_pk_value: str | None = None,
        sort_key_attr: str | None = None,
        expiry_attr: str = "expiration",
        in_progress_expiry_attr: str = "in_progress_expiration",
        status_attr: str = "status",
        data_attr: str = "data",
        validation_key_attr: str = "validation",
        boto_config: Config | None = None,
        boto3_session: boto3.session.Session | None = None,
        boto3_client: DynamoDBClient | None = None,
    ):
        """
        Initialize the DynamoDB client

        Parameters
        ----------
        table_name: str
            Name of the table to use for storing execution records
        key_attr: str, optional
            DynamoDB attribute name for partition key, by default "id"
        static_pk_value: str, optional
            DynamoDB attribute value for partition key, by default "idempotency#<function-name>".
            This will be used if the sort_key_attr is set.
        sort_key_attr: str, optional
            DynamoDB attribute name for the sort key
        expiry_attr: str, optional
            DynamoDB attribute name for expiry timestamp, by default "expiration"
        in_progress_expiry_attr: str, optional
            DynamoDB attribute name for in-progress expiry timestamp, by default "in_progress_expiration"
        status_attr: str, optional
            DynamoDB attribute name for status, by default "status"
        data_attr: str, optional
            DynamoDB attribute name for response data, by default "data"
        validation_key_attr: str, optional
            DynamoDB attribute name for hashed representation of the parts of the event used for validation
        boto_config: botocore.config.Config, optional
            Botocore configuration to pass during client initialization
        boto3_session : boto3.session.Session, optional
            Boto3 session to use for AWS API communication
        boto3_client : DynamoDBClient, optional
            Boto3 DynamoDB Client to use, boto3_session and boto_config will be ignored if both are provided

        Examples
        --------
        **Create a DynamoDB persistence layer with custom settings**

            >>> from aws_lambda_powertools.utilities.idempotency import (
            >>>    idempotent, DynamoDBPersistenceLayer
            >>> )
            >>>
            >>> persistence_store = DynamoDBPersistenceLayer(table_name="idempotency_store")
            >>>
            >>> @idempotent(persistence_store=persistence_store)
            >>> def handler(event, context):
            >>>     return {"StatusCode": 200}
        """
        if boto3_client is None:
            boto3_session = boto3_session or boto3.session.Session()
            boto3_client = boto3_session.client("dynamodb", config=boto_config)
        self.client = boto3_client

        user_agent.register_feature_to_client(client=self.client, feature="idempotency")

        if sort_key_attr == key_attr:
            raise ValueError(
                f"key_attr [{key_attr}] and sort_key_attr [{sort_key_attr}] cannot be the same!"
            )

        if static_pk_value is None:
            static_pk_value = f"idempotency#{os.getenv(constants.LAMBDA_FUNCTION_NAME_ENV, '')}"

        self.table_name = table_name
        self.key_attr = key_attr
        self.static_pk_value = static_pk_value
        self.sort_key_attr = sort_key_attr
        self.expiry_attr = expiry_attr
        self.in_progress_expiry_attr = in_progress_expiry_attr
        self.status_attr = status_attr
        self.data_attr = data_attr
        self.validation_key_attr = validation_key_attr

        # Use DynamoDB's ReturnValuesOnConditionCheckFailure to optimize put and get operations and optimize costs.
        # This feature is supported in boto3 versions 1.26.164 and later.
        self.return_value_on_condition = (
            {"ReturnValuesOnConditionCheckFailure": "ALL_OLD"}
            if self.boto3_supports_condition_check_failure(boto3.__version__)
            else {}
        )

        self._deserializer = TypeDeserializer()

        super().__init__()

    def _get_key(self, idempotency_key: str) -> dict:
        """Build primary key attribute simple or composite based on params.

        When sort_key_attr is set, we must return a composite key with static_pk_value,
        otherwise we use the idempotency key given.

        Parameters
        ----------
        idempotency_key : str
            idempotency key to use for simple primary key

        Returns
        -------
        dict
            simple or composite key for DynamoDB primary key
        """
        if self.sort_key_attr:
            return {
                self.key_attr: {"S": self.static_pk_value},
                self.sort_key_attr: {"S": idempotency_key},
            }
        return {self.key_attr: {"S": idempotency_key}}

    def _item_to_data_record(self, item: dict[str, Any]) -> DataRecord:
        """
        Translate raw item records from DynamoDB to DataRecord

        Parameters
        ----------
        item: dict[str, str | int]
            Item format from dynamodb response

        Returns
        -------
        DataRecord
            representation of item

        """
        data = self._deserializer.deserialize({"M": item})
        return DataRecord(
            idempotency_key=data[self.key_attr],
            status=data[self.status_attr],
            expiry_timestamp=data[self.expiry_attr],
            in_progress_expiry_timestamp=data.get(self.in_progress_expiry_attr),
            response_data=data.get(self.data_attr),
            payload_hash=data.get(self.validation_key_attr),
        )

    def _get_record(self, idempotency_key) -> DataRecord:
        response = self.client.get_item(
            TableName=self.table_name,
            Key=self._get_key(idempotency_key),
            ConsistentRead=True,
        )
        try:
            item = response["Item"]
        except KeyError as exc:
            raise IdempotencyItemNotFoundError from exc
        return self._item_to_data_record(item)

    def _put_record(self, data_record: DataRecord) -> None:
        item = {
            # get simple or composite primary key
            **self._get_key(data_record.idempotency_key),
            self.expiry_attr: {"N": str(data_record.expiry_timestamp)},
            self.status_attr: {"S": data_record.status},
        }

        if data_record.in_progress_expiry_timestamp is not None:
            item[self.in_progress_expiry_attr] = {
                "N": str(data_record.in_progress_expiry_timestamp)
            }

        if self.payload_validation_enabled and data_record.payload_hash:
            item[self.validation_key_attr] = {"S": data_record.payload_hash}

        now = datetime.datetime.now()
        try:
            logger.debug(f"Putting record for idempotency key: {data_record.idempotency_key}")

            # |     LOCKED     |         RETRY if status = "INPROGRESS"                |     RETRY
            # |----------------|-------------------------------------------------------|-------------> .... (time)
            # |             Lambda                                              Idempotency Record
            # |             Timeout                                                 Timeout
            # |       (in_progress_expiry)                                          (expiry)

            # Conditions to successfully save a record:

            # The idempotency key does not exist:
            #    - first time that this invocation key is used
            #    - previous invocation with the same key was deleted due to TTL
            idempotency_key_not_exist = "attribute_not_exists(#id)"

            # The idempotency record exists but it's expired:
            idempotency_expiry_expired = "#expiry < :now"

            # The status of the record is "INPROGRESS", there is an in-progress expiry timestamp, but it's expired
            inprogress_expiry_expired = " AND ".join(
                [
                    "#status = :inprogress",
                    "attribute_exists(#in_progress_expiry)",
                    "#in_progress_expiry < :now_in_millis",
                ],
            )

            condition_expression = f"{idempotency_key_not_exist} OR {idempotency_expiry_expired} OR ({inprogress_expiry_expired})"

            self.client.put_item(
                TableName=self.table_name,
                Item=item,
                ConditionExpression=condition_expression,
                ExpressionAttributeNames={
                    "#id": self.key_attr,
                    "#expiry": self.expiry_attr,
                    "#in_progress_expiry": self.in_progress_expiry_attr,
                    "#status": self.status_attr,
                },
                ExpressionAttributeValues={
                    ":now": {"N": str(int(now.timestamp()))},
                    ":now_in_millis": {"N": str(int(now.timestamp() * 1000))},
                    ":inprogress": {"S": STATUS_CONSTANTS["INPROGRESS"]},
                },
                **self.return_value_on_condition,  # type: ignore[arg-type]
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code == "ConditionalCheckFailedException":
                try:
                    item = exc.response["Item"]  # type: ignore[typeddict-item]
                except KeyError:
                    logger.debug(
                        f"Failed to put record for already existing idempotency key: {data_record.idempotency_key}",
                    )
                    raise IdempotencyItemAlreadyExistsError() from exc
                else:
                    old_data_record = self._item_to_data_record(item)
                    logger.debug(
                        f"Failed to put record for already existing idempotency key: "
                        f"{data_record.idempotency_key} with status: {old_data_record.status}, "
                        f"expiry_timestamp: {old_data_record.expiry_timestamp}, "
                        f"and in_progress_expiry_timestamp: {old_data_record.in_progress_expiry_timestamp}",
                    )

                    try:
                        self._validate_payload(
                            data_payload=data_record, stored_data_record=old_data_record
                        )
                        self._save_to_cache(data_record=old_data_record)
                    except IdempotencyValidationError as idempotency_validation_error:
                        raise idempotency_validation_error from exc

                    raise IdempotencyItemAlreadyExistsError(
                        old_data_record=old_data_record
                    ) from exc

            raise

    @staticmethod
    def boto3_supports_condition_check_failure(boto3_version: str) -> bool:
        """
        Check if the installed boto3 version supports condition check failure.

        Params
        ------
        boto3_version: str
            The boto3 version

        Returns
        -------
        bool
            True if the boto3 version supports condition check failure, False otherwise.
        """
        # Only supported in boto3 1.26.164 and above
        major, minor, *patch = map(int, boto3_version.split("."))
        return (major, minor, *patch) >= (1, 26, 164)

    def _update_record(self, data_record: DataRecord):
        logger.debug(f"Updating record for idempotency key: {data_record.idempotency_key}")
        update_expression = (
            "SET #response_data = :response_data, #expiry = :expiry, #status = :status"
        )
        expression_attr_values: dict[str, AttributeValueTypeDef] = {
            ":expiry": {"N": str(data_record.expiry_timestamp)},
            ":response_data": {"S": data_record.response_data},
            ":status": {"S": data_record.status},
        }
        expression_attr_names = {
            "#expiry": self.expiry_attr,
            "#response_data": self.data_attr,
            "#status": self.status_attr,
        }

        if self.payload_validation_enabled:
            update_expression += ", #validation_key = :validation_key"
            expression_attr_values[":validation_key"] = {"S": data_record.payload_hash}
            expression_attr_names["#validation_key"] = self.validation_key_attr

        self.client.update_item(
            TableName=self.table_name,
            Key=self._get_key(data_record.idempotency_key),
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attr_names,
            ExpressionAttributeValues=expression_attr_values,
        )

    def _delete_record(self, data_record: DataRecord) -> None:
        logger.debug(f"Deleting record for idempotency key: {data_record.idempotency_key}")
        self.client.delete_item(
            TableName=self.table_name, Key={**self._get_key(data_record.idempotency_key)}
        )
