import json

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    Stack,
)
from aws_cdk import (
    aws_apigateway as apigw,
)
from aws_cdk import (
    aws_cloudwatch as cloudwatch,
)
from aws_cdk import (
    aws_cloudwatch_actions as cw_actions,
)
from aws_cdk import (
    aws_dynamodb as dynamodb,
)
from aws_cdk import (
    aws_ec2 as ec2,
)
from aws_cdk import (
    aws_iam as iam,
)
from aws_cdk import (
    aws_kms as kms,
)
from aws_cdk import (
    aws_lambda as _lambda,
)
from aws_cdk import (
    aws_logs as logs,
)
from aws_cdk import (
    aws_opensearchserverless as opensearch,
)
from aws_cdk import (
    aws_s3 as s3,
)
from aws_cdk import (
    aws_sns as sns,
)
from constructs import Construct
from layers.layer_stack import LayerStack


class InfraStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str,
        cert_arn: str,
        layer_stack: LayerStack,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.domain_name = domain_name
        self.cert_arn = cert_arn
        self.layer_stack = layer_stack

        # KMS 키 생성 (보안 강화)
        self._create_kms_key()

        # SNS 알람 토픽
        self._create_sns_topic()

        # VPC 및 네트워크
        self._create_network()

        # OpenSearch Serverless
        self._create_opensearch()

        # DynamoDB
        self._create_dynamodb()

        # S3
        self._create_s3()

        # Lambda 함수들
        self._create_lambda_functions()

        # API Gateway
        self._create_api_gateway()

        # CloudWatch 대시보드 및 알람
        self._create_monitoring()

    def _create_kms_key(self):
        """전용 KMS 키 생성 - 최소 권한 원칙 적용"""
        self.kms_key = kms.Key(
            self,
            "GovChatKMSKey",
            description="GovChat encryption key for sensitive data",
            enable_key_rotation=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        # KMS 키 정책 - Lambda 역할만 접근 허용
        self.kms_key.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowLambdaAccess",
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("lambda.amazonaws.com")],
                actions=["kms:Decrypt", "kms:DescribeKey"],
                conditions={"StringEquals": {"aws:SourceAccount": cdk.Aws.ACCOUNT_ID}},
            )
        )

    def _create_sns_topic(self):
        """알람 전송용 SNS 토픽"""
        self.alarm_topic = sns.Topic(
            self, "GovChatAlarms", topic_name="GovChat-Alarms", display_name="GovChat System Alarms"
        )

        # 알람 토픽 ARN 출력
        cdk.CfnOutput(self, "AlarmTopicArn", value=self.alarm_topic.topic_arn)

    def _create_network(self):
        """네트워크 설정"""
        self.vpc = ec2.Vpc.from_lookup(self, "DefaultVPC", is_default=True)

    def _create_opensearch(self):
        """OpenSearch Serverless - Public 액세스"""
        # 네트워크 정책 - Public 액세스 (임시로 되돌림)
        self.network_policy = opensearch.CfnSecurityPolicy(
            self,
            "NetworkPolicy",
            name="govchat-network-policy-v3",
            type="network",
            policy=json.dumps(
                [
                    {
                        "Rules": [
                            {
                                "ResourceType": "collection",
                                "Resource": ["collection/govchat-vectors-v3"],
                            }
                        ],
                        "AllowFromPublic": True,
                    }
                ]
            ),
        )

        # 암호화 정책
        self.encryption_policy = opensearch.CfnSecurityPolicy(
            self,
            "EncryptionPolicy",
            name="govchat-encryption-policy-v3",
            type="encryption",
            policy=json.dumps(
                {
                    "Rules": [
                        {
                            "ResourceType": "collection",
                            "Resource": ["collection/govchat-vectors-v3"],
                        }
                    ],
                    "AWSOwnedKey": True,
                }
            ),
        )

        # 데이터 액세스 정책
        self.data_access_policy = opensearch.CfnAccessPolicy(
            self,
            "DataAccessPolicy",
            name="govchat-data-access-policy-v3",
            type="data",
            policy=json.dumps(
                [
                    {
                        "Rules": [
                            {
                                "ResourceType": "collection",
                                "Resource": ["collection/govchat-vectors-v3"],
                                "Permission": ["aoss:*"],
                            },
                            {
                                "ResourceType": "index",
                                "Resource": ["index/govchat-vectors-v3/*"],
                                "Permission": ["aoss:*"],
                            },
                        ],
                        "Principal": [f"arn:aws:iam::{cdk.Aws.ACCOUNT_ID}:root"],
                    }
                ]
            ),
        )

        # 벡터 컬렉션
        self.vector_collection = opensearch.CfnCollection(
            self, "VectorCollection", name="govchat-vectors-v3", type="VECTORSEARCH"
        )
        self.vector_collection.add_dependency(self.network_policy)
        self.vector_collection.add_dependency(self.encryption_policy)
        self.vector_collection.add_dependency(self.data_access_policy)

    def _create_dynamodb(self):
        """DynamoDB 테이블"""
        # 스테이지별 RemovalPolicy 설정
        stage = self.node.try_get_context("stage") or "dev"
        removal_policy = cdk.RemovalPolicy.RETAIN if stage == "prod" else cdk.RemovalPolicy.DESTROY
        
        self.cache_table = dynamodb.Table(
            self,
            "CacheTable",
            table_name="govchat-cache-v3",
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="sk", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
            time_to_live_attribute="ttl",  # TTL 지원 추가
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),  # 백업 활성화
        )

        # A3: 사용자 프로필 테이블
        self.user_profile_table = dynamodb.Table(
            self,
            "UserProfileTable",
            table_name="UserProfileTable",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
        )

        # A2: 정책 버전 테이블
        self.policy_version_table = dynamodb.Table(
            self,
            "PolicyVersionTable",
            table_name="PolicyVersionTable",
            partition_key=dynamodb.Attribute(name="policy_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="version", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
        )

        # A2: 정책 메인 테이블
        self.policies_table = dynamodb.Table(
            self,
            "PoliciesTable",
            table_name="PoliciesTable",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
        )

        # 통합 사용자 테이블 (일반, 관리자, 마스터)
        self.users_table = dynamodb.Table(
            self,
            "UsersTable",
            table_name="Users",
            partition_key=dynamodb.Attribute(name="email", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
        )
        
        # 기존 UserTable (호환성 유지)
        self.user_table = dynamodb.Table(
            self,
            "UserTable",
            table_name="UserTable",
            partition_key=dynamodb.Attribute(name="email", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            encryption=dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.kms_key,
        )

    def _create_s3(self):
        """S3 버킷"""
        self.data_bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=f"govchat-data-v3-{cdk.Aws.ACCOUNT_ID}",
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=self.kms_key,
            versioned=True,
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

    def _create_lambda_functions(self):
        """Lambda 함수들"""
        # 공통 환경변수
        common_env = {
            "OPENSEARCH_HOST": self.vector_collection.attr_collection_endpoint.replace(
                "https://", ""
            ),
            "CACHE_TABLE": self.cache_table.table_name,
            "DATA_BUCKET": self.data_bucket.bucket_name,
            "PYTHONIOENCODING": "UTF-8",
            "REQUIRE_AUTH": "false",  # 개발 단계에서는 비활성화
            "VALID_API_KEYS": "dev-key-12345,test-key-67890",  # 개발용 API 키
            "API_KEY_SECRET": "dev-secret-key",
            "KMS_KEY_ID": self.kms_key.key_id,
            "AWS_XRAY_TRACING_NAME": "GovChat",
        }

        # 로그 그룹 사전 정의 (권한 최소화)
        self.log_groups = {}
        lambda_names = [
            "ChatbotLambda",
            "SearchLambda",
            "MatchLambda",
            "ExtractLambda",
            "AdminAuthLambda",
            "PolicyLambda",
            "UserProfileLambda",
            "ExternalSyncLambda",
        ]

        for name in lambda_names:
            self.log_groups[name] = logs.LogGroup(
                self,
                f"{name}LogGroup",
                log_group_name=f"/aws/lambda/GovChat-{name}",
                retention=logs.RetentionDays.ONE_WEEK,
                removal_policy=cdk.RemovalPolicy.DESTROY,
            )

        # 챗봇 Lambda (통합 - 대화형 + 단순 질문)
        self.chatbot_lambda = _lambda.Function(
            self,
            "ChatbotLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="functions.chatbot_handler.handler",
            code=_lambda.Code.from_asset("src"),
            environment=common_env,
            timeout=Duration.seconds(30),
            memory_size=512,
            tracing=_lambda.Tracing.ACTIVE,
            log_group=self.log_groups["ChatbotLambda"],
            layers=self.layer_stack.get_layers_for_function("chatbot"),
        )

        # 검색 Lambda
        self.search_lambda = _lambda.Function(
            self,
            "SearchLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="functions.search_handler.handler",
            code=_lambda.Code.from_asset("src"),
            environment=common_env,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            log_group=self.log_groups["SearchLambda"],
            layers=self.layer_stack.get_layers_for_function("search"),
        )

        # 매칭 Lambda
        self.match_lambda = _lambda.Function(
            self,
            "MatchLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="functions.match_handler.handler",
            code=_lambda.Code.from_asset("src"),
            environment=common_env,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            log_group=self.log_groups["MatchLambda"],
            layers=self.layer_stack.get_layers_for_function("match"),
        )

        # 추출 Lambda
        self.extract_lambda = _lambda.Function(
            self,
            "ExtractLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="functions.extract_handler.handler",
            code=_lambda.Code.from_asset("src"),
            environment=common_env,
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            log_group=self.log_groups["ExtractLambda"],
            layers=self.layer_stack.get_layers_for_function("extract"),
        )

        # A1: 관리자 인증 Lambda
        self.admin_auth_lambda = _lambda.Function(
            self,
            "AdminAuthLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="functions.admin_auth_handler.handler",
            code=_lambda.Code.from_asset("src"),
            environment={**common_env, "USER_PROFILE_TABLE": self.user_profile_table.table_name},
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            log_group=self.log_groups["AdminAuthLambda"],
            layers=self.layer_stack.get_layers_for_function("admin_auth"),
        )

        # A2: 정책 CRUD Lambda
        self.policy_lambda = _lambda.Function(
            self,
            "PolicyLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="functions.policy_handler.handler",
            code=_lambda.Code.from_asset("src"),
            environment={
                **common_env,
                "POLICIES_TABLE": self.policies_table.table_name,
                "POLICY_VERSION_TABLE": self.policy_version_table.table_name,
            },
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            log_group=self.log_groups["PolicyLambda"],
            layers=self.layer_stack.get_layers_for_function("policy"),
        )

        # A3: 사용자 프로필 Lambda
        self.user_profile_lambda = _lambda.Function(
            self,
            "UserProfileLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="functions.user_profile_handler.handler",
            code=_lambda.Code.from_asset("src"),
            environment={**common_env, "USER_PROFILE_TABLE": self.user_profile_table.table_name},
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            log_group=self.log_groups["UserProfileLambda"],
            layers=self.layer_stack.get_layers_for_function("user_profile"),
        )

        # B1: 사용자 인증 Lambda
        self.user_auth_lambda = _lambda.Function(
            self,
            "UserAuthLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="functions.user_auth_handler.handler",
            code=_lambda.Code.from_asset("src"),
            environment={**common_env, "USER_TABLE": "UserTable"},
            timeout=Duration.seconds(30),
            memory_size=256,
            tracing=_lambda.Tracing.ACTIVE,
            layers=self.layer_stack.get_layers_for_function("user_auth"),
        )

        # 외부 데이터 동기화 Lambda
        self.external_sync_lambda = _lambda.Function(
            self,
            "ExternalSyncLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="functions.external_data_sync_handler.handler",
            code=_lambda.Code.from_asset("src"),
            environment=common_env,
            timeout=Duration.seconds(60),
            memory_size=512,
            tracing=_lambda.Tracing.ACTIVE,
            layers=self.layer_stack.get_layers_for_function("external_sync"),
            log_group=self.log_groups["ExternalSyncLambda"],
        )

        # 권한 설정
        functions = [
            self.chatbot_lambda,
            self.search_lambda,
            self.match_lambda,
            self.extract_lambda,
            self.admin_auth_lambda,
            self.policy_lambda,
            self.user_profile_lambda,
            self.user_auth_lambda,
            self.external_sync_lambda,
        ]
        for func in functions:
            self.cache_table.grant_read_write_data(func)
            self.data_bucket.grant_read_write(func)

            # A2, A3: 새로운 테이블 권한
            if func in [self.policy_lambda, self.admin_auth_lambda]:
                self.policies_table.grant_read_write_data(func)
                self.policy_version_table.grant_read_write_data(func)

            if func in [self.user_profile_lambda, self.match_lambda]:
                self.user_profile_table.grant_read_write_data(func)

            if func == self.user_auth_lambda:
                self.user_table.grant_read_write_data(func)
                self.users_table.grant_read_write_data(func)
                
            # 관리자 관리 기능을 위한 Users 테이블 권한
            if func in [self.admin_auth_lambda, self.policy_lambda]:
                self.users_table.grant_read_write_data(func)

            # OpenSearch 권한
            func.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["aoss:APIAccess"], resources=[self.vector_collection.attr_arn]
                )
            )

            # 최소 권한 원칙 적용
            if func == self.chatbot_lambda:
                # 챗봇만 Lambda 호출 권한 필요
                func.add_to_role_policy(
                    iam.PolicyStatement(
                        actions=["lambda:InvokeFunction"],
                        resources=[
                            self.search_lambda.function_arn,
                            self.match_lambda.function_arn,
                            self.extract_lambda.function_arn,
                        ],
                    )
                )

            # CloudWatch 메트릭 권한 (제한적)
            func.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["cloudwatch:PutMetricData"],
                    resources=["*"],
                    conditions={"StringEquals": {"cloudwatch:namespace": "GovChat"}},
                )
            )

            # X-Ray 추적 권한
            func.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["xray:PutTraceSegments", "xray:PutTelemetryRecords"], resources=["*"]
                )
            )

            # KMS 키 사용 권한
            self.kms_key.grant_decrypt(func)

            # Parameter Store 권한 - 스테이지별 리소스 필터링
            stage = self.node.try_get_context("stage") or "dev"
            func.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["ssm:GetParameter", "ssm:GetParameters"],
                    resources=[f"arn:aws:ssm:*:*:parameter/govchat/{stage}/*"],
                    conditions={
                        "StringEquals": {
                            "ssm:SourceAccount": cdk.Aws.ACCOUNT_ID
                        }
                    }
                )
            )
            
            # KMS 키 사용 권한 - Parameter Store 복호화용
            func.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["kms:Decrypt", "kms:DescribeKey"],
                    resources=[self.kms_key.key_arn],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": f"ssm.{cdk.Aws.REGION}.amazonaws.com"
                        }
                    }
                )
            )

    def _create_api_gateway(self):
        """API Gateway"""
        self.api = apigw.RestApi(
            self,
            "GovChatAPI",
            rest_api_name="GovChat API v3",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"],
            ),
        )

        # 공통 메소드 옵션
        method_options = apigw.MethodOptions(authorization_type=apigw.AuthorizationType.NONE)

        # /question 엔드포인트 (챗봇 통합)
        question_resource = self.api.root.add_resource("question")
        question_resource.add_method("POST", apigw.LambdaIntegration(self.chatbot_lambda))

        # /chat 엔드포인트 (대화형 챗봇)
        chat_resource = self.api.root.add_resource("chat")
        chat_resource.add_method("POST", apigw.LambdaIntegration(self.chatbot_lambda))

        # /search 엔드포인트
        search_resource = self.api.root.add_resource("search")
        search_resource.add_method("GET", apigw.LambdaIntegration(self.search_lambda))
        search_resource.add_method("POST", apigw.LambdaIntegration(self.search_lambda))

        # /match 엔드포인트
        match_resource = self.api.root.add_resource("match")
        match_resource.add_method("POST", apigw.LambdaIntegration(self.match_lambda))

        # /extract 엔드포인트
        extract_resource = self.api.root.add_resource("extract")
        extract_resource.add_method("POST", apigw.LambdaIntegration(self.extract_lambda))

        # A1: 관리자 인증 엔드포인트
        admin_resource = self.api.root.add_resource("admin")
        auth_resource = admin_resource.add_resource("auth")
        auth_resource.add_method("POST", apigw.LambdaIntegration(self.admin_auth_lambda))

        # A2: 정책 CRUD 엔드포인트
        policies_resource = self.api.root.add_resource("policies")
        policies_resource.add_method("GET", apigw.LambdaIntegration(self.policy_lambda))
        policies_resource.add_method("POST", apigw.LambdaIntegration(self.policy_lambda))

        policy_id_resource = policies_resource.add_resource("{id}")
        policy_id_resource.add_method("GET", apigw.LambdaIntegration(self.policy_lambda))
        policy_id_resource.add_method("PUT", apigw.LambdaIntegration(self.policy_lambda))

        publish_resource = policy_id_resource.add_resource("publish")
        publish_resource.add_method("POST", apigw.LambdaIntegration(self.policy_lambda))

        # 외부 데이터 동기화 엔드포인트
        sync_resource = admin_resource.add_resource("sync-policies")
        sync_resource.add_method("POST", apigw.LambdaIntegration(self.external_sync_lambda))
        
        search_external_resource = admin_resource.add_resource("search-external")
        search_external_resource.add_method("GET", apigw.LambdaIntegration(self.external_sync_lambda))

        # A3: 사용자 프로필 엔드포인트
        users_resource = self.api.root.add_resource("users")
        user_id_resource = users_resource.add_resource("{uid}")
        profile_resource = user_id_resource.add_resource("profile")
        profile_resource.add_method("GET", apigw.LambdaIntegration(self.user_profile_lambda))
        profile_resource.add_method("PUT", apigw.LambdaIntegration(self.user_profile_lambda))

        # B1: 사용자 인증 엔드포인트
        auth_resource = self.api.root.add_resource("auth")
        user_auth_resource = auth_resource.add_resource("user")

        signup_resource = user_auth_resource.add_resource("signup")
        signup_resource.add_method("POST", apigw.LambdaIntegration(self.user_auth_lambda))

        user_login_resource = user_auth_resource.add_resource("login")
        user_login_resource.add_method("POST", apigw.LambdaIntegration(self.user_auth_lambda))

        # 출력값
        cdk.CfnOutput(self, "APIEndpoint", value=self.api.url)
        cdk.CfnOutput(
            self, "OpenSearchEndpoint", value=self.vector_collection.attr_collection_endpoint
        )

    def _create_monitoring(self):
        """고도화된 모니터링 및 알람 설정"""

        # Lambda 함수별 에러율 알람
        functions = {
            "Chatbot": self.chatbot_lambda,
            "Search": self.search_lambda,
            "Match": self.match_lambda,
            "Extract": self.extract_lambda,
        }

        error_alarms = []
        latency_alarms = []

        for name, func in functions.items():
            # 에러율 알람 (2% 초과)
            error_alarm = cloudwatch.Alarm(
                self,
                f"{name}ErrorAlarm",
                alarm_name=f"GovChat-{name}-ErrorRate",
                alarm_description=f"{name} Lambda error rate > 2%",
                metric=func.metric_errors(period=Duration.minutes(5), statistic="Sum"),
                threshold=2,
                evaluation_periods=2,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            error_alarms.append(error_alarm)

            # P95 지연 알람 (1초 초과)
            latency_alarm = cloudwatch.Alarm(
                self,
                f"{name}LatencyAlarm",
                alarm_name=f"GovChat-{name}-P95Latency",
                alarm_description=f"{name} Lambda P95 latency > 1s",
                metric=func.metric_duration(period=Duration.minutes(5), statistic="p95"),
                threshold=1000,
                evaluation_periods=2,
                treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            )
            latency_alarms.append(latency_alarm)

        # Composite Alarm - 에러율 및 지연 결합
        composite_alarm = cloudwatch.CompositeAlarm(
            self,
            "GovChatSystemAlarm",
            alarm_description="GovChat system health composite alarm",
            alarm_rule=cloudwatch.AlarmRule.any_of(
                *[
                    cloudwatch.AlarmRule.from_alarm(alarm, cloudwatch.AlarmState.ALARM)
                    for alarm in error_alarms + latency_alarms
                ]
            ),
        )

        # SNS 알람 연결
        for alarm in error_alarms + latency_alarms:
            alarm.add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        composite_alarm.add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        # DynamoDB 알람
        dynamodb_throttle_alarm = cloudwatch.Alarm(
            self,
            "DynamoDBThrottleAlarm",
            alarm_name="GovChat-DynamoDB-Throttles",
            alarm_description="DynamoDB throttling detected",
            metric=cloudwatch.Metric(
                namespace="AWS/DynamoDB",
                metric_name="ThrottledRequests",
                dimensions_map={"TableName": self.cache_table.table_name},
                period=Duration.minutes(5),
                statistic="Sum",
            ),
            threshold=1,
            evaluation_periods=1,
        )
        dynamodb_throttle_alarm.add_alarm_action(cw_actions.SnsAction(self.alarm_topic))

        # CloudWatch 대시보드
        dashboard = cloudwatch.Dashboard(
            self, "GovChatDashboard", dashboard_name="GovChat-Operations"
        )

        # Lambda 메트릭 위젯
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Error Rates",
                left=[
                    func.metric_errors(period=Duration.minutes(5)) for func in functions.values()
                ],
                width=12,
                height=6,
            ),
            cloudwatch.GraphWidget(
                title="Lambda Duration (P95)",
                left=[
                    func.metric_duration(period=Duration.minutes(5), statistic="p95")
                    for func in functions.values()
                ],
                width=12,
                height=6,
            ),
        )

        # 캐시 효율 위젯 (사용자 정의 메트릭)
        cache_efficiency_widget = cloudwatch.GraphWidget(
            title="Cache Efficiency %",
            left=[
                cloudwatch.Metric(
                    namespace="GovChat",
                    metric_name="CacheHitRate",
                    period=Duration.minutes(5),
                    statistic="Average",
                )
            ],
            width=12,
            height=6,
        )
        dashboard.add_widgets(cache_efficiency_widget)
