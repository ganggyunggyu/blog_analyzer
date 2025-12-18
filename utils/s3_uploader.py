"""AWS S3 이미지 업로드 유틸"""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_S3_BUCKET,
    AWS_S3_REGION,
)


def get_s3_client():
    """S3 클라이언트 반환"""
    if not all([AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET]):
        return None

    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_S3_REGION,
    )


def upload_image_to_s3(
    image_bytes: bytes,
    keyword: str,
    content_type: str = "image/png",
) -> Optional[str]:
    """
    이미지를 S3에 업로드하고 URL 반환

    Args:
        image_bytes: 이미지 바이트 데이터
        keyword: 키워드 (폴더명으로 사용)
        content_type: MIME 타입

    Returns:
        S3 URL 또는 None (실패 시)
    """
    client = get_s3_client()
    if not client:
        print("S3 설정이 없습니다. base64로 반환합니다.")
        return None

    # 파일명 생성: keyword/날짜_uuid.png
    date_str = datetime.now().strftime("%Y%m%d")
    file_id = str(uuid.uuid4())[:8]
    ext = "png" if "png" in content_type else "jpg"
    key = f"images/{keyword}/{date_str}_{file_id}.{ext}"

    print(f"[S3] 버킷: {AWS_S3_BUCKET}")
    print(f"[S3] 리전: {AWS_S3_REGION}")
    print(f"[S3] 키: {key}")

    try:
        client.put_object(
            Bucket=AWS_S3_BUCKET,
            Key=key,
            Body=image_bytes,
            ContentType=content_type,
        )

        url = f"https://{AWS_S3_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/{key}"
        print(f"[S3] 업로드 완료: {url}")
        return url

    except ClientError as e:
        print(f"S3 업로드 실패: {e}")
        return None
