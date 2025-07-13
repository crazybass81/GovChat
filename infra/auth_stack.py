from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import (
    aws_dynamodb as dynamodb,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_lambda as _lambda,
)
from aws_cdk import (
    aws_ssm as ssm,
)
from constructs import Construct


class AuthStack(Stack):
    """인증 시스템을 위한 CDK 스택"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB 테이블 생성 (NextAuth.js 어댑터용)
        self.auth_table = dynamodb.Table(
            self,
            "AuthTable",
            table_name="govchat-auth",
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,  # 프로덕션 안전성
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
        )

        # GSI 추가 (NextAuth.js 어댑터 요구사항)
        self.auth_table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=dynamodb.Attribute(name="GSI1PK", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="GSI1SK", type=dynamodb.AttributeType.STRING),
        )

        # Lambda Authorizer 함수
        self.jwt_authorizer_function = _lambda.Function(
            self,
            "JwtAuthorizerFunction",
            runtime=_lambda.Runtime.NODEJS_20_X,
            handler="index.handler",
            code=_lambda.Code.from_asset("src/functions/authorizer"),
            environment={
                "NEXTAUTH_SECRET": "temp-secret-will-be-updated-after-deployment",
            },
            timeout=Duration.seconds(30),
        )

        # API Gateway Request Authorizer
        # Note: Authorizer will be attached to RestApi in main InfraStack

        # SSM Parameters for OAuth credentials
        self.create_oauth_parameters()

        # IAM 권한 설정
        self.setup_permissions()

    def create_oauth_parameters(self):
        """OAuth 제공자 설정을 위한 SSM 파라미터 생성"""

        # Google OAuth
        ssm.StringParameter(
            self,
            "GoogleClientId",
            parameter_name="/govchat/auth/google/client-id",
            string_value="SET_YOUR_GOOGLE_CLIENT_ID",
            description="Google OAuth Client ID",
        )

        ssm.StringParameter(
            self,
            "GoogleClientSecret",
            parameter_name="/govchat/auth/google/client-secret",
            string_value="SET_YOUR_GOOGLE_CLIENT_SECRET",
            description="Google OAuth Client Secret",
        )

        # Kakao OAuth
        ssm.StringParameter(
            self,
            "KakaoClientId",
            parameter_name="/govchat/auth/kakao/client-id",
            string_value="SET_YOUR_KAKAO_CLIENT_ID",
            description="Kakao OAuth Client ID",
        )

        ssm.StringParameter(
            self,
            "KakaoClientSecret",
            parameter_name="/govchat/auth/kakao/client-secret",
            string_value="SET_YOUR_KAKAO_CLIENT_SECRET",
            description="Kakao OAuth Client Secret",
        )

        # Naver OAuth
        ssm.StringParameter(
            self,
            "NaverClientId",
            parameter_name="/govchat/auth/naver/client-id",
            string_value="SET_YOUR_NAVER_CLIENT_ID",
            description="Naver OAuth Client ID",
        )

        ssm.StringParameter(
            self,
            "NaverClientSecret",
            parameter_name="/govchat/auth/naver/client-secret",
            string_value="SET_YOUR_NAVER_CLIENT_SECRET",
            description="Naver OAuth Client Secret",
        )

        # NextAuth Secret
        ssm.StringParameter(
            self,
            "NextAuthSecret",
            parameter_name="/govchat/auth/nextauth-secret",
            string_value="your-super-secret-jwt-secret-key-32-chars-minimum",
            description="NextAuth.js JWT Secret",
        )

    def setup_permissions(self):
        """IAM 권한 설정"""

        # Lambda Authorizer에 SSM 읽기 권한 부여
        self.jwt_authorizer_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["ssm:GetParameter", "ssm:GetParameters", "ssm:GetParametersByPath"],
                resources=[f"arn:aws:ssm:{self.region}:{self.account}:parameter/govchat/auth/*"],
            )
        )

        # NextAuth.js가 DynamoDB 테이블에 접근할 수 있도록 권한 부여
        # (실제로는 Next.js 애플리케이션의 실행 환경에서 설정해야 함)
        self.auth_table.grant_read_write_data(self.jwt_authorizer_function)
