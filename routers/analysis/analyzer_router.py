from __future__ import annotations
from typing import Dict, List
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from analyzer.morpheme import analyze_morphemes
from analyzer.sentence import split_sentences
from analyzer.expression import gen_expressions
from analyzer.parameter import parameter_gen
from analyzer.subtitle import gen_subtitles
from analyzer.template import template_gen
from analyzer.library import build_sentence_library
from utils.txt_file_parser import parse_txt_file


router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    text: str
    category: str = ""
    file_name: str = ""


class MorphemeResponse(BaseModel):
    morphemes: List[str]
    count: int


class SentenceResponse(BaseModel):
    sentences: List[str]
    count: int


class ExpressionResponse(BaseModel):
    expressions: Dict[str, List[str]]
    total_count: int


class ParameterResponse(BaseModel):
    parameters: Dict[str, List[str]]
    total_count: int


class SubtitleResponse(BaseModel):
    subtitles: List[str]
    count: int


class TemplateRequest(BaseModel):
    user_instructions: str
    docs: str
    category: str
    file_name: str = ""


class TemplateResponse(BaseModel):
    templated_text: str


class TxtFileAnalysisResponse(BaseModel):
    parsed_data: Dict[str, str]
    morphemes: List[str]
    sentences: List[str]
    expressions: Dict[str, List[str]]
    parameters: Dict[str, List[str]]
    subtitles: List[str]
    templated_text: str


@router.post("/morpheme", response_model=MorphemeResponse)
async def analyze_morpheme_endpoint(request: AnalyzeRequest):
    """형태소 분석 API"""
    try:
        morphemes = await run_in_threadpool(
            analyze_morphemes, request.text, request.category, request.file_name
        )
        return MorphemeResponse(morphemes=morphemes, count=len(morphemes))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"형태소 분석 오류: {e}")


@router.post("/sentence", response_model=SentenceResponse)
async def split_sentence_endpoint(request: AnalyzeRequest):
    """문장 분리 API"""
    try:
        sentences = await run_in_threadpool(
            split_sentences, request.text, request.category, request.file_name
        )
        return SentenceResponse(sentences=sentences, count=len(sentences))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문장 분리 오류: {e}")


@router.post("/expression", response_model=ExpressionResponse)
async def extract_expression_endpoint(request: AnalyzeRequest):
    """표현 추출 API"""
    try:
        expressions = await run_in_threadpool(
            gen_expressions, request.text, request.category, request.file_name
        )
        total_count = sum(len(exprs) for exprs in expressions.values())
        return ExpressionResponse(expressions=expressions, total_count=total_count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"표현 추출 오류: {e}")


@router.post("/parameter", response_model=ParameterResponse)
async def extract_parameter_endpoint(request: AnalyzeRequest):
    """파라미터 추출 API"""
    try:
        parameters = await run_in_threadpool(
            parameter_gen, request.text, request.category, request.file_name
        )
        total_count = sum(len(pars) for pars in parameters.values())
        return ParameterResponse(parameters=parameters, total_count=total_count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파라미터 추출 오류: {e}")


@router.post("/subtitle", response_model=SubtitleResponse)
async def extract_subtitle_endpoint(request: AnalyzeRequest):
    """부제목 추출 API"""
    try:
        subtitles = await run_in_threadpool(
            gen_subtitles, request.text, request.category, request.file_name
        )
        return SubtitleResponse(subtitles=subtitles, count=len(subtitles))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"부제목 추출 오류: {e}")


@router.post("/template", response_model=TemplateResponse)
async def generate_template_endpoint(request: TemplateRequest):
    """템플릿 생성 API"""
    try:
        templated_text = await run_in_threadpool(
            template_gen,
            request.user_instructions,
            request.docs,
            request.category,
            request.file_name,
        )
        return TemplateResponse(templated_text=templated_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"템플릿 생성 오류: {e}")


class LibraryRequest(BaseModel):
    directory_path: str
    category: str = ""


class LibraryResponse(BaseModel):
    library: Dict[str, List[str]]
    total_sentences: int


@router.post("/library", response_model=LibraryResponse)
async def build_library_endpoint(request: LibraryRequest):
    """문장 라이브러리 구축 API"""
    try:
        library = await run_in_threadpool(
            build_sentence_library, request.directory_path, request.category
        )
        total_sentences = sum(len(sentences) for sentences in library.values())
        return LibraryResponse(library=library, total_sentences=total_sentences)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"라이브러리 구축 오류: {e}")


class AllAnalysisRequest(BaseModel):
    text: str
    category: str
    file_name: str = ""


class AllAnalysisResponse(BaseModel):
    morphemes: List[str]
    sentences: List[str]
    expressions: Dict[str, List[str]]
    parameters: Dict[str, List[str]]
    subtitles: List[str]
    templated_text: str


@router.post("/all", response_model=AllAnalysisResponse)
async def analyze_all_endpoint(request: AllAnalysisRequest):
    """모든 분석을 한 번에 수행하는 API"""
    try:

        morphemes = await run_in_threadpool(
            analyze_morphemes, request.text, request.category, request.file_name
        )

        sentences = await run_in_threadpool(
            split_sentences, request.text, request.category, request.file_name
        )

        expressions = await run_in_threadpool(
            gen_expressions, request.text, request.category, request.file_name
        )

        parameters = await run_in_threadpool(
            parameter_gen, request.text, request.category, request.file_name
        )

        subtitles = await run_in_threadpool(
            gen_subtitles, request.text, request.category, request.file_name
        )
        templated_text = await run_in_threadpool(
            template_gen, "", request.text, request.category, request.file_name
        )

        return AllAnalysisResponse(
            morphemes=morphemes,
            sentences=sentences,
            expressions=expressions,
            parameters=parameters,
            subtitles=subtitles,
            templated_text=templated_text,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"전체 분석 오류: {e}")


@router.post("/txt-all", response_model=TxtFileAnalysisResponse)
async def analyze_txt_file_endpoint(file: UploadFile = File(...)):
    """
    txt 파일을 업로드해서 전체 분석을 수행하는 테스트 API
    """
    try:

        if not file.filename or not file.filename.endswith(".txt"):
            raise HTTPException(status_code=400, detail="txt 파일만 업로드 가능합니다.")

        file_content = await file.read()

        parsed_data = await run_in_threadpool(
            parse_txt_file, file_content, file.filename
        )

        text = parsed_data["text"]
        category = parsed_data["category"]
        file_name = parsed_data["file_name"]

        morphemes = await run_in_threadpool(
            analyze_morphemes, text, category, file_name
        )

        sentences = await run_in_threadpool(split_sentences, text, category, file_name)

        expressions = await run_in_threadpool(
            gen_expressions, text, category, file_name
        )

        parameters = await run_in_threadpool(parameter_gen, text, category, file_name)

        subtitles = await run_in_threadpool(gen_subtitles, text, category, file_name)

        templated_text = await run_in_threadpool(
            template_gen, "기본 템플릿 생성", text, category, file_name
        )

        return TxtFileAnalysisResponse(
            parsed_data=parsed_data,
            morphemes=morphemes,
            sentences=sentences,
            expressions=expressions,
            parameters=parameters,
            subtitles=subtitles,
            templated_text=templated_text,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"txt 파일 분석 오류: {e}")
