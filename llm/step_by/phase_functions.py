# -*- coding: utf-8 -*-
"""
스텝바이스텝 원고 생성을 위한 각 PHASE별 AI 호출 함수들
"""

import json
import time
from typing import Dict, Any, List, Optional

from _constants.Model import Model
from config import OPENAI_API_KEY, openai_client
from utils.text_cleaner import comprehensive_text_clean
from .prompts import STEP_BY_STEP_PROMPTS

MODEL_NAME = Model.GPT5


def call_openai_with_prompt(prompt: str, max_retries: int = 3) -> str:
    """
    OpenAI API 호출 공통 함수

    Args:
        prompt: 전송할 프롬프트
        max_retries: 최대 재시도 횟수

    Returns:
        AI 응답 텍스트

    Raises:
        ValueError: API 키 미설정
        RuntimeError: AI 응답 오류
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다.")

    for attempt in range(max_retries):
        try:
            print(f"🤖 OpenAI API 호출 중... (시도: {attempt + 1}/{max_retries})")

            response = openai_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 전문적인 SEO 최적화 콘텐츠 작성 전문가입니다.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            if not response.choices or not response.choices[0].message:
                raise RuntimeError("AI가 유효한 응답을 반환하지 않았습니다.")

            result = response.choices[0].message.content.strip()

            if not result:
                raise RuntimeError("AI가 빈 응답을 반환했습니다.")

            # 토큰 사용량 로깅
            if hasattr(response, "usage") and response.usage:
                print(
                    f"📊 토큰 사용량: in={response.usage.prompt_tokens}, out={response.usage.completion_tokens}"
                )

            return result

        except Exception as e:
            print(f"❌ API 호출 실패 (시도 {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                raise RuntimeError(f"OpenAI API 호출 실패: {e}")
            time.sleep(2)  # 재시도 전 대기


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """
    AI 응답에서 JSON 파싱

    Args:
        response_text: AI 응답 텍스트

    Returns:
        파싱된 JSON 딕셔너리
    """
    try:
        # JSON 블록 찾기 - 여러 방법 시도
        json_str = response_text.strip()

        # 1. 전체가 JSON인 경우
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # 2. JSON 블록을 찾는 경우
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1

        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # 3. 코드 블록 안에 있는 경우
        if "```json" in response_text:
            start_marker = response_text.find("```json") + 7
            end_marker = response_text.find("```", start_marker)
            if end_marker != -1:
                json_str = response_text[start_marker:end_marker].strip()
                return json.loads(json_str)

        # 4. 마지막 시도 - 가장 큰 JSON 블록 찾기
        import re

        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.findall(json_pattern, response_text)

        for match in reversed(matches):  # 가장 긴 것부터 시도
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        raise ValueError("유효한 JSON을 찾을 수 없습니다.")

    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        print(f"❌ 응답 텍스트 (처음 500자): {response_text[:500]}")
        raise ValueError(f"JSON 파싱 실패: {e}")


def phase_1_speaker_setting(keyword: str) -> Dict[str, Any]:
    """
    PHASE 1: 화자 설정 및 대분류 도출

    Args:
        keyword: 메인 키워드

    Returns:
        화자 정보와 카테고리
    """
    print(f"🎭 PHASE 1: 화자 설정 시작 - 키워드: {keyword}")

    prompt = STEP_BY_STEP_PROMPTS["phase_1_speaker"].format(keyword=keyword)
    response = call_openai_with_prompt(prompt)

    result = parse_json_response(response)

    print(f"✅ 대분류: {result.get('category', 'N/A')}")
    print(f"✅ 화자 설정 완료")

    return result


def phase_2_generate_subtitles(keyword: str, category: str) -> List[str]:
    """
    PHASE 2: 5개 독립 소제목 생성

    Args:
        keyword: 메인 키워드
        category: 대분류 카테고리

    Returns:
        5개 소제목 리스트
    """
    print(f"📋 PHASE 2: 소제목 생성 시작 - 카테고리: {category}")

    prompt = STEP_BY_STEP_PROMPTS["phase_2_subtitles"].format(
        keyword=keyword, category=category
    )
    response = call_openai_with_prompt(prompt)

    result = parse_json_response(response)
    subtitles = result.get("subtitles", [])

    print(f"✅ 생성된 소제목:")
    for i, subtitle in enumerate(subtitles, 1):
        print(f"   {i}. {subtitle}")

    return subtitles


def phase_3_generate_keywords(
    keyword: str, subtitles: List[str]
) -> Dict[str, List[str]]:
    """
    PHASE 3: 연관키워드 40개 생성

    Args:
        keyword: 메인 키워드
        subtitles: 소제목 리스트

    Returns:
        4개 레이어별 키워드 딕셔너리
    """
    print(f"🔄 PHASE 3: 연관키워드 생성 시작")

    prompt = STEP_BY_STEP_PROMPTS["phase_3_keywords"].format(
        keyword=keyword, subtitles=", ".join(subtitles)
    )
    response = call_openai_with_prompt(prompt)

    result = parse_json_response(response)
    keywords = result.get("keywords", {})

    total_count = sum(len(layer_keywords) for layer_keywords in keywords.values())
    print(f"✅ 연관키워드 {total_count}개 생성 완료")

    for layer, layer_keywords in keywords.items():
        print(f"   {layer}: {len(layer_keywords)}개")

    return keywords


def phase_4_generate_title(
    keyword: str, subtitles: List[str], keywords: Dict[str, List[str]]
) -> List[str]:
    """
    PHASE 4: 제목 생성

    Args:
        keyword: 메인 키워드
        subtitles: 소제목 리스트
        keywords: 연관키워드 딕셔너리

    Returns:
        3개 제목 후보 리스트
    """
    print(f"📝 PHASE 4: 제목 생성 시작")

    prompt = STEP_BY_STEP_PROMPTS["phase_4_title"].format(
        keyword=keyword, subtitles=", ".join(subtitles), keywords=str(keywords)
    )
    response = call_openai_with_prompt(prompt)

    result = parse_json_response(response)
    titles = result.get("titles", [])

    print(f"✅ 제목 후보 {len(titles)}개 생성:")
    for i, title in enumerate(titles, 1):
        print(f"   {i}. {title}")

    return titles


def phase_5_generate_intro(speaker_info: Dict[str, Any], keyword: str) -> str:
    """
    PHASE 5: 도입부 생성

    Args:
        speaker_info: 화자 정보
        keyword: 메인 키워드

    Returns:
        200자 도입부
    """
    print(f"🎬 PHASE 5: 도입부 생성 시작")

    prompt = STEP_BY_STEP_PROMPTS["phase_5_intro"].format(
        speaker_info=str(speaker_info), keyword=keyword
    )
    response = call_openai_with_prompt(prompt)

    result = parse_json_response(response)
    intro = result.get("intro", "")

    print(f"✅ 도입부 생성 완료 ({len(intro)}자)")

    return intro


def phase_6_generate_content(
    subtitle: str,
    speaker_info: Dict[str, Any],
    keywords: Dict[str, List[str]],
    reference: str = "",
) -> str:
    """
    PHASE 6: 각 소제목별 본문 생성

    Args:
        subtitle: 소제목
        speaker_info: 화자 정보
        keywords: 연관키워드 딕셔너리
        reference: 참조 원고

    Returns:
        350자 본문
    """
    print(f"✍️ PHASE 6: 본문 생성 시작 - {subtitle}")

    prompt = STEP_BY_STEP_PROMPTS["phase_6_content"].format(
        subtitle=subtitle,
        speaker_info=str(speaker_info),
        keywords=str(keywords),
        reference=reference,
    )
    response = call_openai_with_prompt(prompt)

    result = parse_json_response(response)
    content = result.get("content", "")

    print(f"✅ 본문 생성 완료 ({len(content)}자)")

    return content


def phase_7_generate_conclusion(
    speaker_info: Dict[str, Any], keyword: str, content_summary: str
) -> str:
    """
    PHASE 7: 마무리 생성

    Args:
        speaker_info: 화자 정보
        keyword: 메인 키워드
        content_summary: 전체 내용 요약

    Returns:
        50자 마무리
    """
    print(f"🏁 PHASE 7: 마무리 생성 시작")

    prompt = STEP_BY_STEP_PROMPTS["phase_7_conclusion"].format(
        speaker_info=str(speaker_info), keyword=keyword, content_summary=content_summary
    )
    response = call_openai_with_prompt(prompt)

    result = parse_json_response(response)
    conclusion = result.get("conclusion", "")

    print(f"✅ 마무리 생성 완료 ({len(conclusion)}자)")

    return conclusion


def phase_8_keyword_check(full_content: str, keyword: str) -> Dict[str, Any]:
    """
    PHASE 8: 키워드 반복 체크 및 수정 (간소화 버전)

    Args:
        full_content: 전체 원고
        keyword: 메인 키워드

    Returns:
        수정된 원고
    """
    print(f"🔍 PHASE 8: 키워드 반복 체크 시작")

    prompt = STEP_BY_STEP_PROMPTS["phase_8_keyword_check"].format(
        full_content=full_content, keyword=keyword
    )
    response = call_openai_with_prompt(prompt)

    result = parse_json_response(response)
    corrected_content = result.get("corrected_content", full_content)

    # 간단한 키워드 카운트 (수동)
    keyword_count = {}
    words_to_check = [keyword, "효과", "복용", "다이어트", "주사"]

    for word in words_to_check:
        count = corrected_content.count(word)
        keyword_count[word] = count

    print(f"✅ 키워드 체크 완료:")
    for word, count in keyword_count.items():
        status = "✅" if count <= 5 else "⚠️"
        print(f"   {status} {word}: {count}회")

    return {"keyword_count": keyword_count, "corrected_content": corrected_content}
