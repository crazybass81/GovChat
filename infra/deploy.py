#!/usr/bin/env python3
"""
배포 스크립트
"""

import subprocess
import sys
import os

def run_command(cmd, cwd=None):
    """명령어 실행"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout

def main():
    print("🚀 GovChat 배포 시작...")
    
    # 1. 테스트 실행
    print("📋 테스트 실행 중...")
    run_command("python3 -m pytest tests/ -v --cov=src --cov-report=html", cwd="/home/ec2-user/gov-support-chat")
    
    # 2. 보안 검사
    print("🔒 보안 검사 중...")
    run_command("bandit -r src/ -f json -o security-report.json", cwd="/home/ec2-user/gov-support-chat/infra")
    
    # 3. CDK 배포
    print("☁️ AWS CDK 배포 중...")
    run_command("cdk bootstrap", cwd="/home/ec2-user/gov-support-chat/infra")
    run_command("cdk deploy --all --require-approval never", cwd="/home/ec2-user/gov-support-chat/infra")
    
    print("✅ 배포 완료!")

if __name__ == "__main__":
    main()