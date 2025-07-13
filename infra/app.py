#!/usr/bin/env python3
import os

import aws_cdk as cdk
from auth_stack import AuthStack
from infra_stack import InfraStack
from layers.layer_stack import LayerStack

# 필수 전역 설정
ACCOUNT_ID = os.getenv("CDK_DEFAULT_ACCOUNT", "123456789012")
REGION = os.getenv("CDK_DEFAULT_REGION", "ap-northeast-2")
DOMAIN_NAME = os.getenv("DOMAIN_NAME", "api.example.com")
CERT_ARN = os.getenv("CERT_ARN", "arn:aws:acm:ap-...")

app = cdk.App()
env = cdk.Environment(account=ACCOUNT_ID, region=REGION)

# 레이어 스택 먼저 생성
layer_stack = LayerStack(
    app,
    "GovChatLayerStack",
    env=env,
)

# 인증 스택 생성
auth_stack = AuthStack(
    app,
    "GovChatAuthStack",
    env=env,
)

# 인프라 스택 생성 (레이어 스택 의존성)
infra_stack = InfraStack(
    app,
    "GovChatStack",
    env=env,
    domain_name=DOMAIN_NAME,
    cert_arn=CERT_ARN,
    layer_stack=layer_stack,
)

# 의존성 설정
infra_stack.add_dependency(layer_stack)
infra_stack.add_dependency(auth_stack)

app.synth()
