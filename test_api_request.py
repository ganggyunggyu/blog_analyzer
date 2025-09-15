# -*- coding: utf-8 -*-
"""
스텝바이스텝 API 테스트 스크립트
"""

import requests
import json
import time

def test_step_by_step_api():
    """스텝바이스텝 API 테스트"""
    url = "http://127.0.0.1:8002/generate/step-by-step"

    # 테스트 데이터
    test_data = {
        "service": "step-by-step",
        "keyword": "삭센다 효과",
        "ref": "다이어트 주사로 유명한 삭센다는 많은 분들이 관심을 가지고 있습니다."
    }

    print("🚀 스텝바이스텝 API 테스트 시작!")
    print(f"📝 키워드: {test_data['keyword']}")
    print(f"📄 참조원고: 있음")
    print("=" * 60)

    try:
        start_time = time.time()

        # API 호출
        response = requests.post(url, json=test_data, timeout=300)  # 5분 타임아웃

        end_time = time.time()

        if response.status_code == 200:
            result = response.json()

            print("✅ API 호출 성공!")
            print(f"⏱️ 소요시간: {end_time - start_time:.1f}초")
            print(f"📊 생성 글자수: {result.get('word_count', 0)}자")
            print(f"📊 생성 문자수: {result.get('character_count', 0)}자")
            print(f"🎭 카테고리: {result.get('category', 'N/A')}")
            print(f"💾 MongoDB ID: {result.get('_id', 'N/A')}")

            print("\n" + "=" * 60)
            print("📝 생성된 원고 (처음 1000자):")
            print("=" * 60)
            content = result.get('content', '')
            print(content[:1000])
            if len(content) > 1000:
                print("\n... (이후 생략)")
            print("=" * 60)

            return True

        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"오류 내용: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ API 호출 타임아웃 (5분 초과)")
        return False
    except Exception as e:
        print(f"❌ API 호출 오류: {e}")
        return False

if __name__ == "__main__":
    test_step_by_step_api()