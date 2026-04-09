"""애견 키워드별 AI 이미지 생성 스크립트

애견/ 하위 키워드 폴더에 키워드명 디렉토리를 만들고 5장씩 생성합니다.
"""

import os
import sys
import time
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from google import genai
from google.genai import types

from config import GEMINI_API_KEY
from _constants.Model import Model
from llm.image_service import build_image_prompt, get_random_pose
from utils.s3_uploader import upload_image_to_s3

MODEL_NAME = Model.GEMINI_2_5_FLASH_IMAGE
COUNT_PER_KEYWORD = 5
PET_DIR = os.path.join(os.path.dirname(__file__), "..", "애견")
CATEGORY = "애견동물_반려동물_분양"


def find_keyword_dirs():
    """애견/ 하위 키워드 폴더 목록"""
    dirs = []
    for blog in sorted(os.listdir(PET_DIR)):
        blog_path = os.path.join(PET_DIR, blog)
        if not os.path.isdir(blog_path):
            continue
        for keyword in sorted(os.listdir(blog_path)):
            keyword_path = os.path.join(blog_path, keyword)
            if os.path.isdir(keyword_path):
                dirs.append((blog, keyword, keyword_path))
    return dirs


def generate_and_save(client, keyword: str, index: int, save_dir: str) -> bool:
    pose = get_random_pose()
    prompt = build_image_prompt(keyword, pose=pose, category=CATEGORY)

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
            print(f"    #{index} 실패: 응답 없음")
            return False

        for part in parts:
            if hasattr(part, "inline_data") and part.inline_data is not None:
                image_data = part.inline_data
                image_bytes = getattr(image_data, "data", None)
                if not image_bytes and hasattr(image_data, "_pb"):
                    image_bytes = image_data._pb.data

                if not image_bytes:
                    continue

                filename = f"{keyword}_{index}.png"
                filepath = os.path.join(save_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(image_bytes)

                s3_url = upload_image_to_s3(
                    image_bytes=image_bytes,
                    keyword=keyword,
                    content_type="image/png",
                )

                s3_status = "S3 ✓" if s3_url else "S3 ✗"
                print(f"    #{index} ✓ ({s3_status}) → {filename}")
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
    keyword_dirs = find_keyword_dirs()

    total_success = 0
    total_fail = 0
    start = time.time()

    print(f"총 {len(keyword_dirs)}개 키워드 발견\n")

    for idx, (blog, keyword, keyword_path) in enumerate(keyword_dirs, 1):
        save_dir = os.path.join(keyword_path, keyword)
        os.makedirs(save_dir, exist_ok=True)

        print(f"[{idx}/{len(keyword_dirs)}] {blog}/{keyword} ({COUNT_PER_KEYWORD}장)")

        for i in range(1, COUNT_PER_KEYWORD + 1):
            filepath = os.path.join(save_dir, f"{keyword}_{i}.png")
            if os.path.exists(filepath):
                print(f"    #{i} 이미 존재 → 건너뜀")
                total_success += 1
                continue
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
