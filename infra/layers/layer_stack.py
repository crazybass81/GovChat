"""
Lambda Layer CDK Stack
4개 레이어를 정의하고 배포하는 스택
"""


import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_lambda as _lambda
from constructs import Construct


class LayerStack(Stack):
    """Lambda Layer 전용 스택"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 레이어 정의
        self.layers = self._create_layers()

        # 출력값 설정
        self._create_outputs()

    def _create_layers(self) -> dict:
        """4개 레이어 생성"""
        layers = {}

        # 1. AWS Core Layer
        layers["aws_core"] = _lambda.LayerVersion(
            self,
            "AWSCoreLayer",
            layer_version_name="govchat-aws-core-v1",
            code=_lambda.Code.from_asset("layers/dist/aws-core-layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="AWS SDK and core utilities for GovChat",
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # 2. Powertools Layer
        layers["powertools"] = _lambda.LayerVersion(
            self,
            "PowertoolsLayer",
            layer_version_name="govchat-powertools-v1",
            code=_lambda.Code.from_asset("layers/dist/powertools-layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="AWS Lambda Powertools and observability for GovChat",
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # 3. Data Processing Layer
        layers["data"] = _lambda.LayerVersion(
            self,
            "DataLayer",
            layer_version_name="govchat-data-v1",
            code=_lambda.Code.from_asset("layers/dist/data-layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="Data processing and validation libraries for GovChat",
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # 4. Search & Security Layer
        layers["search_security"] = _lambda.LayerVersion(
            self,
            "SearchSecurityLayer",
            layer_version_name="govchat-search-security-v1",
            code=_lambda.Code.from_asset("layers/dist/search-security-layer.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="OpenSearch and security libraries for GovChat",
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        return layers

    def _create_outputs(self):
        """레이어 ARN 출력"""
        for name, layer in self.layers.items():
            cdk.CfnOutput(
                self,
                f"{name.title()}LayerArn",
                value=layer.layer_version_arn,
                description=f"ARN of {name} layer",
                export_name=f"GovChat-{name.replace('_', '-')}-Layer-Arn",
            )

    def get_layer_arns(self) -> dict:
        """다른 스택에서 사용할 레이어 ARN 반환"""
        return {name: layer.layer_version_arn for name, layer in self.layers.items()}

    def get_layers_for_function(self, function_type: str) -> list:
        """Lambda 함수 타입별 필요한 레이어 반환"""
        layer_mapping = {
            "chatbot": ["aws_core", "powertools", "data", "search_security"],
            "search": ["aws_core", "powertools", "search_security"],
            "match": ["aws_core", "powertools", "data"],
            "extract": ["aws_core", "powertools", "data"],
            "admin_auth": ["aws_core", "powertools", "search_security"],
            "user_auth": ["aws_core", "powertools", "search_security"],
            "policy": ["aws_core", "powertools", "data"],
            "user_profile": ["aws_core", "powertools", "data"],
        }

        required_layers = layer_mapping.get(function_type, ["aws_core", "powertools"])
        return [self.layers[layer_name] for layer_name in required_layers]
