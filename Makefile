.PHONY: test deploy health-check review clean lint format type-check

# 코드 품질 검사
lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy infra/src/ tests/

# 전체 품질 검사
quality: lint type-check

# 테스트 실행
test:
	cd infra && python -m pytest ../tests/ -v

# 보안 테스트만 실행
test-security:
	cd infra && python -m pytest ../tests/test_security.py -v

# 통합 테스트 실행
test-integration:
	cd infra && python -m pytest ../tests/test_integration.py -v

# CDK 배포
deploy:
	cd infra && cdk deploy --all --require-approval never

# 헬스체크 실행
health-check:
	python scripts/health-check.py

# 코드 리뷰 생성
review:
	python scripts/generate-code-review.py

# 정리
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	cd infra && rm -rf cdk.out

# 전체 파이프라인
pipeline: clean test deploy health-check review