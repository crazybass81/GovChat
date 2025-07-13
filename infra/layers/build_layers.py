#!/usr/bin/env python3
"""
Lambda Layer 빌드 스크립트
각 레이어별로 의존성을 설치하고 ZIP 파일로 패키징
"""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

# 레이어 정의
LAYERS = {
    "aws-core": {
        "requirements": "requirements-aws-core.txt",
        "description": "AWS SDK and core utilities",
    },
    "powertools": {
        "requirements": "requirements-powertools.txt",
        "description": "AWS Lambda Powertools and observability",
    },
    "data": {
        "requirements": "requirements-data.txt",
        "description": "Data processing and validation libraries",
    },
    "search-security": {
        "requirements": "requirements-search-security.txt",
        "description": "OpenSearch and security libraries",
    },
}


def build_layer(layer_name, config):
    """개별 레이어 빌드"""
    print(f"Building layer: {layer_name}")

    # 작업 디렉토리 생성
    build_dir = Path(f"build/{layer_name}")
    python_dir = build_dir / "python"

    # 기존 빌드 디렉토리 제거
    if build_dir.exists():
        shutil.rmtree(build_dir)

    python_dir.mkdir(parents=True)

    # pip install
    cmd = ["pip", "install", "-r", config["requirements"], "-t", str(python_dir)]

    try:
        subprocess.run(cmd, check=True, cwd=Path.cwd())
        print(f"✓ Dependencies installed for {layer_name}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies for {layer_name}: {e}")
        return False

    # ZIP 파일 생성
    zip_path = f"dist/{layer_name}-layer.zip"
    os.makedirs("dist", exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(build_dir)
                zipf.write(file_path, arc_path)

    # 크기 확인
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"✓ Layer {layer_name} created: {zip_path} ({size_mb:.1f}MB)")

    return True


def main():
    """모든 레이어 빌드"""
    print("Starting Lambda Layer build process...")

    # 빌드 디렉토리 초기화
    if Path("build").exists():
        shutil.rmtree("build")
    if Path("dist").exists():
        shutil.rmtree("dist")

    success_count = 0

    for layer_name, config in LAYERS.items():
        if build_layer(layer_name, config):
            success_count += 1
        print("-" * 50)

    print(f"Build completed: {success_count}/{len(LAYERS)} layers successful")

    if success_count == len(LAYERS):
        print("All layers built successfully! Ready for CDK deployment.")
        return 0
    else:
        print("Some layers failed to build. Check errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
