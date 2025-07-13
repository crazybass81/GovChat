#!/bin/bash

echo "🧹 코드베이스 정리 시작..."

# 1. CDK 아티팩트 정리
echo "CDK 빌드 아티팩트 삭제 중..."
rm -rf infra/cdk.out/
rm -rf infra/.cdk/

# 2. Python 캐시 정리
echo "Python 캐시 정리 중..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# 3. Node.js 캐시 정리
echo "Node.js 캐시 정리 중..."
rm -rf frontend/.next/
rm -rf frontend/node_modules/.cache/

# 4. 사용하지 않는 파일 제거
echo "사용하지 않는 파일 제거 중..."
rm -f infra/src/common/database.py
rm -f infra/src/common/api_auth.py
rm -f infra/src/common/data_api_client.py

# 5. .gitignore 업데이트
echo "# Build artifacts" >> .gitignore
echo "infra/cdk.out/" >> .gitignore
echo "infra/.cdk/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "frontend/.next/" >> .gitignore

echo "✅ 정리 완료!"
echo "📊 정리 결과:"
echo "- CDK 빌드 아티팩트 삭제됨"
echo "- Python 캐시 정리됨"
echo "- 사용하지 않는 파일 제거됨"
echo "- .gitignore 업데이트됨"