# -*- coding: utf-8 -*-
"""
Step-by-Step PHASE 1 API 테스트용 스크립트
실제 FastAPI 서버에 요청 보내서 테스트
"""

import requests
import json
import time


def test_step_by_step_api(
    keyword: str, ref: str = "", base_url: str = "http://localhost:8000"
):
    """
    Step-by-Step API 테스트

    Args:
        keyword: 테스트할 키워드
        ref: 참조 원고 (선택적)
        base_url: API 서버 URL

    Returns:
        API 응답 결과
    """
    url = f"{base_url}/generate/step-by-step"

    payload = {"service": "step-by-step", "keyword": keyword, "ref": ref}

    headers = {"Content-Type": "application/json"}

    print(f"🚀 API 요청 시작!")
    print(f"🔗 URL: {url}")
    print(f"📝 키워드: {keyword}")
    print(f"📄 참조원고: {'있음' if ref else '없음'}")
    print("=" * 60)

    start_time = time.time()

    try:
        # API 요청
        response = requests.post(url, json=payload, headers=headers, timeout=300)

        elapsed_time = time.time() - start_time

        print(f"📊 응답 시간: {elapsed_time:.2f}초")
        print(f"📊 상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            print("✅ API 요청 성공!")
            print(f"📊 생성 글자수: {result.get('word_count', 'N/A')}자")
            print(f"📊 문자수: {result.get('character_count', 'N/A')}자")
            print(f"🎭 카테고리: {result.get('category', 'N/A')}")
            print(f"🤖 엔진: {result.get('engine', 'N/A')}")

            # 생성된 내용 일부 미리보기
            content = result.get("content", "")
            if content:
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"\n📄 내용 미리보기:\n{preview}")

            return result

        else:
            print(f"❌ API 요청 실패!")
            print(f"❌ 오류 내용: {response.text}")
            return None

    except requests.exceptions.Timeout:
        print("⏰ 요청 시간 초과 (5분)")
        return None

    except requests.exceptions.ConnectionError:
        print("🔌 서버 연결 실패 - 서버가 실행 중인지 확인하세요!")
        return None

    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return None


def test_step_by_step_info_api(base_url: str = "http://localhost:8000"):
    """
    Step-by-Step 정보 API 테스트

    Args:
        base_url: API 서버 URL

    Returns:
        시스템 정보
    """
    url = f"{base_url}/generate/step-by-step/info"

    print(f"🔍 시스템 정보 API 테스트")
    print(f"🔗 URL: {url}")

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            info = response.json()
            print("✅ 시스템 정보 조회 성공!")
            print(f"🤖 모델: {info.get('model', 'N/A')}")
            print(f"📝 설명: {info.get('description', 'N/A')}")

            features = info.get("features", [])
            if features:
                print(f"\n🎯 기능 목록:")
                for i, feature in enumerate(features, 1):
                    print(f"   {i}. {feature}")

            phases = info.get("phases", [])
            if phases:
                print(f"\n📋 단계 목록:")
                for phase in phases:
                    print(f"   PHASE {phase.get('phase')}: {phase.get('name')}")

            return info

        else:
            print(f"❌ 시스템 정보 조회 실패: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 시스템 정보 조회 오류: {e}")
        return None


def test_step_by_step_detailed_api(
    keyword: str, ref: str = "", base_url: str = "http://localhost:8000"
):
    """
    Step-by-Step 상세 결과 API 테스트

    Args:
        keyword: 테스트할 키워드
        ref: 참조 원고 (선택적)
        base_url: API 서버 URL

    Returns:
        상세 API 응답 결과
    """
    url = f"{base_url}/generate/step-by-step-detailed"

    payload = {"service": "step-by-step-detailed", "keyword": keyword, "ref": ref}

    headers = {"Content-Type": "application/json"}

    print(f"🔬 상세 결과 API 요청 시작!")
    print(f"🔗 URL: {url}")
    print(f"📝 키워드: {keyword}")
    print("=" * 60)

    start_time = time.time()

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=300)

        elapsed_time = time.time() - start_time

        print(f"📊 응답 시간: {elapsed_time:.2f}초")
        print(f"📊 상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            print("✅ 상세 API 요청 성공!")
            print(f"📊 제목: {result.get('title', 'N/A')}")
            print(f"📊 생성 시간: {result.get('generation_time', 'N/A')}초")

            # 소제목 목록
            subtitles = result.get("subtitles", [])
            if subtitles:
                print(f"\n📋 생성된 소제목:")
                for i, subtitle in enumerate(subtitles, 1):
                    print(f"   {i}. {subtitle}")

            # 키워드 사용 현황
            keyword_count = result.get("keyword_count", {})
            if keyword_count:
                print(f"\n🔍 키워드 사용 현황:")
                for word, count in keyword_count.items():
                    status = "✅" if count <= 5 else "⚠️"
                    print(f"   {status} {word}: {count}회")

            return result

        else:
            print(f"❌ 상세 API 요청 실패!")
            print(f"❌ 오류 내용: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 상세 API 테스트 오류: {e}")
        return None


def main():
    """메인 테스트 실행"""
    print("🧪 Step-by-Step API 테스트 스크립트")
    print("=" * 60)

    # 1. 시스템 정보 확인
    print("\n1️⃣ 시스템 정보 확인")
    test_step_by_step_info_api()

    print("\n" + "=" * 60)

    # 2. 기본 API 테스트
    print("\n2️⃣ 기본 원고 생성 API 테스트")
    test_keyword = "위고비 가격"
    basic_result = test_step_by_step_api(test_keyword)

    print("\n" + "=" * 60)

    # 3. 상세 결과 API 테스트
    print("\n3️⃣ 상세 결과 API 테스트")
    detailed_result = test_step_by_step_detailed_api(test_keyword)

    print("\n🎉 모든 API 테스트 완료!")


if __name__ == "__main__":
    # 간단한 테스트
    test_keyword = "위고비"

    print("🔬 단일 API 테스트")
    result = test_step_by_step_api(test_keyword)

    if result:
        print("\n✨ 테스트 성공!")
    else:
        print("\n❌ 테스트 실패!")

    print("\n" + "=" * 60)
    print("💡 전체 테스트를 원하면 main() 함수를 실행하세요!")

    # 전체 테스트 실행하려면 주석 해제
    # main()
