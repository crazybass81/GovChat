from datetime import datetime
from typing import Dict, List, Literal, Type, Union

from aws_lambda_powertools.shared.functions import base64_decode, bytes_to_string
from pydantic import BaseModel, field_validator

SERVERS_DELIMITER = ","


class KafkaRecordModel(BaseModel):
    topic: str
    partition: int
    offset: int
    timestamp: datetime
    timestampType: str
    key: bytes
    value: Union[str, Type[BaseModel]]
    headers: List[Dict[str, bytes]]

    # Added type ignore to keep compatibility between Pydantic v1 and v2
    _decode_key = field_validator("key")(base64_decode)  # type: ignore[type-var, unused-ignore]

    @field_validator("value", mode="before")
    def data_base64_decode(cls, value):
        as_bytes = base64_decode(value)
        return bytes_to_string(as_bytes)

    @field_validator("headers", mode="before")
    def decode_headers_list(cls, value):
        for header in value:
            for key, values in header.items():
                header[key] = bytes(values)
        return value


class KafkaBaseEventModel(BaseModel):
    bootstrapServers: List[str]
    records: Dict[str, List[KafkaRecordModel]]

    @field_validator("bootstrapServers", mode="before")
    def split_servers(cls, value):
        return None if not value else value.split(SERVERS_DELIMITER)


class KafkaSelfManagedEventModel(KafkaBaseEventModel):
    """Self-managed Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-kafka.html
    """

    eventSource: Literal["aws:SelfManagedKafka"]


class KafkaMskEventModel(KafkaBaseEventModel):
    """Fully-managed AWS Apache Kafka event trigger
    Documentation:
    --------------
    - https://docs.aws.amazon.com/lambda/latest/dg/with-msk.html
    """

    eventSource: Literal["aws:kafka"]
    eventSourceArn: str
