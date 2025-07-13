from typing import List

from aws_lambda_powertools.utilities.parser.models.s3 import S3Model
from aws_lambda_powertools.utilities.parser.models.sqs import SqsModel, SqsRecordModel
from pydantic import Json


class S3SqsEventNotificationRecordModel(SqsRecordModel):
    body: Json[S3Model]


class S3SqsEventNotificationModel(SqsModel):
    Records: List[S3SqsEventNotificationRecordModel]
