# -*- coding: utf-8 -*-
"""
스텝바이스텝 원고 생성 API 라우터
10단계 PHASE를 순차적으로 실행하여 SEO 최적화 원고 생성
"""

import time
from fastapi import HTTPException, APIRouter
from fastapi.concurrency import run_in_threadpool

from _constants.Model import Model
from mongodb_service import MongoDBService
from utils.get_category_db_name import get_category_db_name
from utils.progress_logger import progress
from schema.generate import GenerateRequest
from llm.step_by import step_by_step_generate, step_by_step_generate_detailed

router = APIRouter()
MODEL_NAME = Model.GPT5


@router.post("/generate/step-by-step")
async def generate_step_by_step_manuscript(request: GenerateRequest):
    """
    스텝바이스텝 원고 생성 API

    10단계 PHASE를 통해 SEO 최적화된 2000자 원고 생성:
    1. 화자 설정 및 대분류 도출
    2. 5개 독립 소제목 생성
    3. 연관키워드 40개 생성
    4. 제목 생성
    5. 도입부 생성 (200자)
    6. 본문 생성 (350자 × 5개)
    7. 마무리 생성 (50자)
    8. 키워드 반복 체크 및 수정

    Args:
        request: GenerateRequest
            - service: 서비스명
            - keyword: 메인 키워드
            - ref: 참조 원고 (선택적)

    Returns:
        생성된 원고 문서
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref_content = request.ref

    if not keyword:
        raise HTTPException(status_code=400, detail="키워드가 없습니다.")

    # 카테고리 자동 분류
    category = get_category_db_name(keyword=keyword)

    # MongoDB 서비스 초기화
    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    # 디버그 로깅
    is_ref = bool(ref_content and ref_content.strip())
    print(
        f"[STEP-BY-STEP] service={service} | model={MODEL_NAME} | category={category} | keyword={keyword} | has_ref={is_ref}"
    )

    try:
        # 스텝바이스텝 원고 생성 (프로그레스 표시)
        with progress(label=f"step-by-step:{MODEL_NAME}"):
            generated_manuscript = await run_in_threadpool(
                step_by_step_generate, keyword=keyword, reference=ref_content
            )

        if not generated_manuscript:
            raise HTTPException(
                status_code=500, detail="스텝바이스텝 원고 생성에 실패했습니다."
            )

        # MongoDB에 저장
        current_time = time.time()
        document = {
            "content": generated_manuscript,
            "timestamp": current_time,
            "engine": MODEL_NAME,
            "keyword": keyword,
            "category": category,
            "service": "step-by-step",
            "word_count": len(generated_manuscript.replace(" ", "")),
            "character_count": len(generated_manuscript),
        }

        try:
            result_id = db_service.insert_document("manuscripts", document)
            document["_id"] = str(result_id)

            print(f"✅ 스텝바이스텝 원고 저장 완료: {result_id}")
            print(f"📊 생성 글자수: {document['word_count']}자")

            return document

        except Exception as db_error:
            print(f"❌ DB 저장 실패: {db_error}")
            # DB 저장 실패해도 원고는 반환
            return {
                "content": generated_manuscript,
                "timestamp": current_time,
                "engine": MODEL_NAME,
                "keyword": keyword,
                "category": category,
                "service": "step-by-step",
                "word_count": len(generated_manuscript.replace(" ", "")),
                "character_count": len(generated_manuscript),
                "_id": "db_save_failed",
            }

    except ValueError as ve:
        print(f"❌ 입력 오류: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except RuntimeError as re:
        print(f"❌ 실행 오류: {re}")
        raise HTTPException(status_code=500, detail=str(re))

    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"스텝바이스텝 원고 생성 중 오류: {e}"
        )

    finally:
        # 리소스 정리
        if db_service:
            db_service.close_connection()


@router.post("/generate/step-by-step-detailed")
async def generate_step_by_step_detailed(request: GenerateRequest):
    """
    스텝바이스텝 원고 생성 API (상세 결과 포함)

    모든 단계별 결과와 메타데이터를 함께 반환합니다.

    Returns:
        완성된 원고 + 모든 PHASE별 결과 + 메타데이터
    """
    service = request.service.lower()
    keyword = request.keyword.strip()
    ref_content = request.ref

    if not keyword:
        raise HTTPException(status_code=400, detail="키워드가 없습니다.")

    # 카테고리 자동 분류
    category = get_category_db_name(keyword=keyword)

    # MongoDB 서비스 초기화
    db_service = MongoDBService()
    db_service.set_db_name(db_name=category)

    # 디버그 로깅
    is_ref = bool(ref_content and ref_content.strip())
    print(
        f"[STEP-BY-STEP-DETAILED] service={service} | model={MODEL_NAME} | category={category} | keyword={keyword} | has_ref={is_ref}"
    )

    try:
        # 스텝바이스텝 상세 원고 생성
        with progress(label=f"step-by-step-detailed:{MODEL_NAME}"):
            detailed_result = await run_in_threadpool(
                step_by_step_generate_detailed, keyword=keyword, reference=ref_content
            )

        if not detailed_result or not detailed_result.get("content"):
            raise HTTPException(
                status_code=500, detail="스텝바이스텝 상세 원고 생성에 실패했습니다."
            )

        # 상세 문서 구성
        current_time = time.time()
        detailed_document = {
            "content": detailed_result["content"],
            "title": detailed_result.get("title", ""),
            "timestamp": current_time,
            "engine": MODEL_NAME,
            "keyword": keyword,
            "category": category,
            "service": "step-by-step-detailed",
            "word_count": detailed_result.get("word_count", 0),
            "character_count": detailed_result.get("character_count", 0),
            "generation_time": detailed_result.get("generation_time", 0),
            # 스텝바이스텝 상세 정보
            "speaker_info": detailed_result.get("speaker_info", {}),
            "subtitles": detailed_result.get("subtitles", []),
            "keywords": detailed_result.get("keywords", {}),
            "keyword_count": detailed_result.get("keyword_count", {}),
            "all_phases": detailed_result.get("all_phases", {}),
        }

        try:
            result_id = db_service.insert_document(
                "manuscripts_detailed", detailed_document
            )
            detailed_document["_id"] = str(result_id)

            print(f"✅ 스텝바이스텝 상세 원고 저장 완료: {result_id}")
            print(f"📊 생성 글자수: {detailed_document['word_count']}자")
            print(f"⏱️ 생성시간: {detailed_document['generation_time']:.1f}초")

            return detailed_document

        except Exception as db_error:
            print(f"❌ DB 저장 실패: {db_error}")
            # DB 저장 실패해도 결과는 반환
            detailed_document["_id"] = "db_save_failed"
            return detailed_document

    except ValueError as ve:
        print(f"❌ 입력 오류: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))

    except RuntimeError as re:
        print(f"❌ 실행 오류: {re}")
        raise HTTPException(status_code=500, detail=str(re))

    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        raise HTTPException(
            status_code=500, detail=f"스텝바이스텝 상세 원고 생성 중 오류: {e}"
        )

    finally:
        # 리소스 정리
        if db_service:
            db_service.close_connection()


@router.get("/generate/step-by-step/info")
async def get_step_by_step_info():
    """
    스텝바이스텝 원고 생성 시스템 정보 API

    Returns:
        시스템 정보와 사용 방법
    """
    return {
        "service": "step-by-step",
        "model": MODEL_NAME,
        "description": "10단계 PHASE를 통한 SEO 최적화 원고 생성",
        "features": [
            "화자 페르소나 자동 설정",
            "5개 독립 소제목 생성",
            "연관키워드 40개 확장",
            "키워드 반복 5회 제한",
            "정확한 2000자 분량",
            "경험담 중심 구성",
            "SEO 최적화 구조",
        ],
        "phases": [
            {"phase": 1, "name": "화자 설정 및 대분류 도출"},
            {"phase": 2, "name": "5개 독립 소제목 생성"},
            {"phase": 3, "name": "연관키워드 40개 생성"},
            {"phase": 4, "name": "제목 생성"},
            {"phase": 5, "name": "도입부 생성 (200자)"},
            {"phase": 6, "name": "본문 생성 (350자 × 5개)"},
            {"phase": 7, "name": "마무리 생성 (50자)"},
            {"phase": 8, "name": "키워드 반복 체크 및 수정"},
        ],
        "endpoints": [
            {
                "path": "/generate/step-by-step",
                "method": "POST",
                "description": "기본 스텝바이스텝 원고 생성",
            },
            {
                "path": "/generate/step-by-step-detailed",
                "method": "POST",
                "description": "상세 결과 포함 원고 생성",
            },
        ],
        "usage": {
            "request": {
                "service": "step-by-step",
                "keyword": "메인 키워드 (필수)",
                "ref": "참조 원고 (선택)",
            },
            "example": {
                "service": "step-by-step",
                "keyword": "위고비 가격",
                "ref": "기존 다이어트 관련 원고...",
            },
        },
    }
