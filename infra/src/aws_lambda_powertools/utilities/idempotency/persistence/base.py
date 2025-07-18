"""
Persistence layers supporting idempotency
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import jmespath
from aws_lambda_powertools.shared import constants
from aws_lambda_powertools.shared.cache_dict import LRUDict
from aws_lambda_powertools.shared.json_encoder import Encoder
from aws_lambda_powertools.utilities.idempotency.exceptions import (
    IdempotencyItemAlreadyExistsError,
    IdempotencyKeyError,
    IdempotencyValidationError,
)
from aws_lambda_powertools.utilities.idempotency.persistence.datarecord import (
    STATUS_CONSTANTS,
    DataRecord,
)
from aws_lambda_powertools.utilities.jmespath_utils import PowertoolsFunctions

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.idempotency.config import IdempotencyConfig

logger = logging.getLogger(__name__)


class BasePersistenceLayer(ABC):
    """
    Abstract Base Class for Idempotency persistence layer.
    """

    def __init__(self):
        """Initialize the defaults"""
        self.function_name = ""
        self.configured = False
        self.event_key_jmespath: str = ""
        self.event_key_compiled_jmespath = None
        self.jmespath_options: dict | None = None
        self.payload_validation_enabled = False
        self.validation_key_jmespath = None
        self.raise_on_no_idempotency_key = False
        self.expires_after_seconds: int = 60 * 60  # 1 hour default
        self.use_local_cache = False
        self.hash_function = hashlib.md5

    def configure(self, config: IdempotencyConfig, function_name: str | None = None) -> None:
        """
        Initialize the base persistence layer from the configuration settings

        Parameters
        ----------
        config: IdempotencyConfig
            Idempotency configuration settings
        function_name: str, Optional
            The name of the function being decorated
        """
        self.function_name = (
            f"{os.getenv(constants.LAMBDA_FUNCTION_NAME_ENV, 'test-func')}.{function_name or ''}"
        )

        if self.configured:
            # Prevent being reconfigured multiple times
            return
        self.configured = True

        self.event_key_jmespath = config.event_key_jmespath
        if config.event_key_jmespath:
            self.event_key_compiled_jmespath = jmespath.compile(config.event_key_jmespath)
        self.jmespath_options = config.jmespath_options
        if not self.jmespath_options:
            self.jmespath_options = {"custom_functions": PowertoolsFunctions()}
        if config.payload_validation_jmespath:
            self.validation_key_jmespath = jmespath.compile(config.payload_validation_jmespath)
            self.payload_validation_enabled = True
        self.raise_on_no_idempotency_key = config.raise_on_no_idempotency_key
        self.expires_after_seconds = config.expires_after_seconds
        self.use_local_cache = config.use_local_cache
        if self.use_local_cache:
            self._cache = LRUDict(max_items=config.local_cache_max_items)
        self.hash_function = getattr(hashlib, config.hash_function)

    def _get_hashed_idempotency_key(self, data: dict[str, Any]) -> str | None:
        """
        Extract idempotency key and return a hashed representation

        Parameters
        ----------
        data: dict[str, Any]
            Incoming data

        Returns
        -------
        str
            Hashed representation of the data extracted by the jmespath expression

        """
        if self.event_key_jmespath:
            data = self.event_key_compiled_jmespath.search(
                data, options=jmespath.Options(**self.jmespath_options)
            )

        if self.is_missing_idempotency_key(data=data):
            if self.raise_on_no_idempotency_key:
                raise IdempotencyKeyError("No data found to create a hashed idempotency_key")

            warnings.warn(
                f"No idempotency key value found. Skipping persistence layer and validation operations. jmespath: {self.event_key_jmespath}",  # noqa: E501
                stacklevel=2,
            )
            return None

        generated_hash = self._generate_hash(data=data)
        return f"{self.function_name}#{generated_hash}"

    @staticmethod
    def is_missing_idempotency_key(data) -> bool:
        if isinstance(data, (tuple, list, dict)):
            return all(x is None for x in data)
        elif isinstance(data, (int, float, bool)):
            return False
        return not data

    def _get_hashed_payload(self, data: dict[str, Any]) -> str:
        """
        Extract payload using validation key jmespath and return a hashed representation

        Parameters
        ----------
        data: dict[str, Any]
            Payload

        Returns
        -------
        str
            Hashed representation of the data extracted by the jmespath expression

        """
        if not self.payload_validation_enabled:
            return ""
        data = self.validation_key_jmespath.search(data)
        return self._generate_hash(data=data)

    def _generate_hash(self, data: Any) -> str:
        """
        Generate a hash value from the provided data

        Parameters
        ----------
        data: Any
            The data to hash

        Returns
        -------
        str
            Hashed representation of the provided data

        """
        hashed_data = self.hash_function(json.dumps(data, cls=Encoder, sort_keys=True).encode())
        return hashed_data.hexdigest()

    def _validate_payload(
        self,
        data_payload: dict[str, Any] | DataRecord,
        stored_data_record: DataRecord,
    ) -> None:
        """
        Validate that the hashed payload matches data provided and stored data record

        Parameters
        ----------
        data_payload: dict[str, Any] | DataRecord
            Payload
        stored_data_record: DataRecord
            DataRecord fetched from Dynamo or cache

        Raises
        ----------
        IdempotencyValidationError
            Payload doesn't match the stored record for the given idempotency key

        """
        if self.payload_validation_enabled:
            if isinstance(data_payload, DataRecord):
                data_hash = data_payload.payload_hash
            else:
                data_hash = self._get_hashed_payload(data=data_payload)

            if stored_data_record.payload_hash != data_hash:
                raise IdempotencyValidationError(
                    "Payload does not match stored record for this event key"
                )

    def _get_expiry_timestamp(self) -> int:
        """

        Returns
        -------
        int
            unix timestamp of expiry date for idempotency record

        """
        now = datetime.datetime.now()
        period = datetime.timedelta(seconds=self.expires_after_seconds)
        return int((now + period).timestamp())

    def _save_to_cache(self, data_record: DataRecord):
        """
        Save data_record to local cache except when status is "INPROGRESS"

        NOTE: We can't cache "INPROGRESS" records as we have no way to reflect updates that can happen outside of the
        execution environment

        Parameters
        ----------
        data_record: DataRecord
            DataRecord instance

        Returns
        -------

        """
        if not self.use_local_cache:
            return
        if data_record.status == STATUS_CONSTANTS["INPROGRESS"]:
            return
        self._cache[data_record.idempotency_key] = data_record

    def _retrieve_from_cache(self, idempotency_key: str):
        if not self.use_local_cache:
            return
        cached_record = self._cache.get(key=idempotency_key)
        if cached_record:
            if not cached_record.is_expired:
                return cached_record
            logger.debug(
                f"Removing expired local cache record for idempotency key: {idempotency_key}"
            )
            self._delete_from_cache(idempotency_key=idempotency_key)

    def _delete_from_cache(self, idempotency_key: str):
        if not self.use_local_cache:
            return
        if idempotency_key in self._cache:
            del self._cache[idempotency_key]

    def save_success(self, data: dict[str, Any], result: dict) -> None:
        """
        Save record of function's execution completing successfully

        Parameters
        ----------
        data: dict[str, Any]
            Payload
        result: dict
            The response from function
        """
        idempotency_key = self._get_hashed_idempotency_key(data=data)
        if idempotency_key is None:
            # If the idempotency key is None, no data will be saved in the Persistence Layer.
            # See: https://github.com/aws-powertools/powertools-lambda-python/issues/2465
            return None

        response_data = json.dumps(result, cls=Encoder, sort_keys=True)

        data_record = DataRecord(
            idempotency_key=idempotency_key,
            status=STATUS_CONSTANTS["COMPLETED"],
            expiry_timestamp=self._get_expiry_timestamp(),
            response_data=response_data,
            payload_hash=self._get_hashed_payload(data=data),
        )
        logger.debug(
            f"Function successfully executed. Saving record to persistence store with "
            f"idempotency key: {data_record.idempotency_key}",
        )
        self._update_record(data_record=data_record)

        self._save_to_cache(data_record=data_record)

    def save_inprogress(
        self, data: dict[str, Any], remaining_time_in_millis: int | None = None
    ) -> None:
        """
        Save record of function's execution being in progress

        Parameters
        ----------
        data: dict[str, Any]
            Payload
        remaining_time_in_millis: int | None
            If expiry of in-progress invocations is enabled, this will contain the remaining time available in millis
        """

        idempotency_key = self._get_hashed_idempotency_key(data=data)
        if idempotency_key is None:
            # If the idempotency key is None, no data will be saved in the Persistence Layer.
            # See: https://github.com/aws-powertools/powertools-lambda-python/issues/2465
            return None

        data_record = DataRecord(
            idempotency_key=idempotency_key,
            status=STATUS_CONSTANTS["INPROGRESS"],
            expiry_timestamp=self._get_expiry_timestamp(),
            payload_hash=self._get_hashed_payload(data=data),
        )

        # When Lambda kills the container after timeout, the remaining_time_in_millis is 0, which is considered False.
        # Therefore, we need to check if remaining_time_in_millis is not None (>=0) to handle this case.
        # See: https://github.com/aws-powertools/powertools-lambda-python/issues/4759
        if remaining_time_in_millis is not None:
            now = datetime.datetime.now()
            period = datetime.timedelta(milliseconds=remaining_time_in_millis)
            timestamp = (now + period).timestamp()
            data_record.in_progress_expiry_timestamp = int(timestamp * 1000)
        else:
            warnings.warn(
                "Couldn't determine the remaining time left. "
                "Did you call register_lambda_context on IdempotencyConfig?",
                stacklevel=2,
            )

        logger.debug(
            f"Saving in progress record for idempotency key: {data_record.idempotency_key}"
        )

        if self._retrieve_from_cache(idempotency_key=data_record.idempotency_key):
            raise IdempotencyItemAlreadyExistsError

        self._put_record(data_record=data_record)

    def delete_record(self, data: dict[str, Any], exception: Exception):
        """
        Delete record from the persistence store

        Parameters
        ----------
        data: dict[str, Any]
            Payload
        exception
            The exception raised by the function
        """

        idempotency_key = self._get_hashed_idempotency_key(data=data)
        if idempotency_key is None:
            # If the idempotency key is None, no data will be saved in the Persistence Layer.
            # See: https://github.com/aws-powertools/powertools-lambda-python/issues/2465
            return None

        data_record = DataRecord(idempotency_key=idempotency_key)

        logger.debug(
            f"Function raised an exception ({type(exception).__name__}). Clearing in progress record in persistence "
            f"store for idempotency key: {data_record.idempotency_key}",
        )
        self._delete_record(data_record=data_record)

        self._delete_from_cache(idempotency_key=data_record.idempotency_key)

    def get_record(self, data: dict[str, Any]) -> DataRecord | None:
        """
        Retrieve idempotency key for data provided, fetch from persistence store, and convert to DataRecord.

        Parameters
        ----------
        data: dict[str, Any]
            Payload

        Returns
        -------
        DataRecord
            DataRecord representation of existing record found in persistence store

        Raises
        ------
        IdempotencyItemNotFoundError
            Exception raised if no record exists in persistence store with the idempotency key
        IdempotencyValidationError
            Payload doesn't match the stored record for the given idempotency key
        """

        idempotency_key = self._get_hashed_idempotency_key(data=data)
        if idempotency_key is None:
            # If the idempotency key is None, no data will be saved in the Persistence Layer.
            # See: https://github.com/aws-powertools/powertools-lambda-python/issues/2465
            return None

        cached_record = self._retrieve_from_cache(idempotency_key=idempotency_key)
        if cached_record:
            logger.debug(
                f"Idempotency record found in cache with idempotency key: {idempotency_key}"
            )
            self._validate_payload(data_payload=data, stored_data_record=cached_record)
            return cached_record

        record = self._get_record(idempotency_key=idempotency_key)

        self._validate_payload(data_payload=data, stored_data_record=record)
        self._save_to_cache(data_record=record)

        return record

    @abstractmethod
    def _get_record(self, idempotency_key) -> DataRecord:
        """
        Retrieve item from persistence store using idempotency key and return it as a DataRecord instance.

        Parameters
        ----------
        idempotency_key

        Returns
        -------
        DataRecord
            DataRecord representation of existing record found in persistence store

        Raises
        ------
        IdempotencyItemNotFoundError
            Exception raised if no record exists in persistence store with the idempotency key
        """
        raise NotImplementedError

    @abstractmethod
    def _put_record(self, data_record: DataRecord) -> None:
        """
        Add a DataRecord to persistence store if it does not already exist with that key. Raise ItemAlreadyExists
        if a non-expired entry already exists.

        Parameters
        ----------
        data_record: DataRecord
            DataRecord instance
        """

        raise NotImplementedError

    @abstractmethod
    def _update_record(self, data_record: DataRecord) -> None:
        """
        Update item in persistence store

        Parameters
        ----------
        data_record: DataRecord
            DataRecord instance
        """

        raise NotImplementedError

    @abstractmethod
    def _delete_record(self, data_record: DataRecord) -> None:
        """
        Remove item from persistence store
        Parameters
        ----------
        data_record: DataRecord
            DataRecord instance
        """

        raise NotImplementedError
