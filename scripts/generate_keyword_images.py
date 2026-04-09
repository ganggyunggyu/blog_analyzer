"""키워드별 AI 이미지 생성 스크립트

각 키워드 폴더의 개별사진/ 디렉토리에 5장씩 생성합니다.
S3 업로드도 동시에 진행됩니다.
"""

import os
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from google import genai
from google.genai import types
from io import BytesIO

from config import GEMINI_API_KEY
from _constants.Model import Model
from llm.image_service import build_image_prompt
from utils.s3_uploader import upload_image_to_s3

MODEL_NAME = Model.GEMINI_2_5_FLASH_IMAGE
COUNT_PER_KEYWORD = 5
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "키워드")

KEYWORDS = [
    "스마일라식 비용",
    "스마일라식 통증",
    "라식 부작용",
    "스마일프로",
    "라식 재수술",
    "스마일라식 회복기간",
    "스마일라식 라식 차이",
    "라식 라섹 차이",
    "라섹",
    "라식",
    "라식라섹",
    "렌즈삽입술",
]


def generate_and_save(client, keyword: str, index: int, save_dir: str) -> bool:
    prompt = build_image_prompt(keyword, pose="", category="")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        parts = getattr(response, "parts", None)
        if not parts and hasattr(response, "candidates") and response.candidates:
            parts = response.candidates[0].content.parts

        if not parts:
            print(f"    #{index} 실패: 응답 없음 (정책 거부 가능)")
            return False

        for part in parts:
            if hasattr(part, "inline_data") and part.inline_data is not None:
                image_bytes = None
                image_data = part.inline_data

                if hasattr(image_data, "data"):
                    image_bytes = image_data.data
                elif hasattr(image_data, "_pb") and hasattr(image_data._pb, "data"):
                    image_bytes = image_data._pb.data

                if not image_bytes:
                    continue

                # 로컬 저장
                filename = f"{keyword}_{index}_{uuid.uuid4().hex[:8]}.png"
                filepath = os.path.join(save_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(image_bytes)

                # S3 업로드
                s3_url = upload_image_to_s3(
                    image_bytes=image_bytes,
                    keyword=keyword,
                    content_type="image/png",
                )

                s3_status = "S3 ✓" if s3_url else "S3 ✗"
                print(f"    #{index} ✓ 저장 완료 ({s3_status}) → {filename}")
                return True

        print(f"    #{index} 실패: 이미지 데이터 없음")
        return False

    except Exception as e:
        print(f"    #{index} 실패: {e}")
        return False


def main():
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY가 설정되어 있지 않습니다.")
        sys.exit(1)

    client = genai.Client(api_key=GEMINI_API_KEY)

    total_success = 0
    total_fail = 0
    start = time.time()

    for keyword in KEYWORDS:
        save_dir = os.path.join(BASE_DIR, keyword, "개별사진")
        os.makedirs(save_dir, exist_ok=True)

        print(f"\n{'='*50}")
        print(f"  {keyword} ({COUNT_PER_KEYWORD}장)")
        print(f"{'='*50}")

        for i in range(1, COUNT_PER_KEYWORD + 1):
            success = generate_and_save(client, keyword, i, save_dir)
            if success:
                total_success += 1
            else:
                total_fail += 1
            time.sleep(1)

    elapsed = time.time() - start
    print(f"\n{'='*50}")
    print(f"  완료: {total_success}장 성공, {total_fail}장 실패 ({elapsed:.1f}s)")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
