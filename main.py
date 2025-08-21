# -*- coding: utf-8 -*-
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional

import click
from tqdm import tqdm

# 내부 모듈 (경로는 네 프로젝트에 맞게)
from mongodb_service import MongoDBService
from analyzer.morpheme import analyze_morphemes
from analyzer.sentence import split_sentences
from analyzer.expression import extract_expressions_with_ai
from analyzer.parameter import extract_and_group_entities_with_ai
from analyzer.template import generate_template_from_segment
from analyzer.library import build_sentence_library
from llm.gpt_4_service import gpt_4_gen
from analyzer.subtitle import extract_subtitles_with_ai
from config import OPENAI_API_KEY

# ---------- 공통 유틸 ----------
API_DELAY_EXPR = 1.0   # 표현/파라미터 추출 호출 간 지연
API_DELAY_TMPL = 0.5   # 템플릿 생성 호출 간 지연

def _ensure_dir(directory_path: str) -> Path:
    p = Path(directory_path)
    if not p.exists() or not p.is_dir():
        raise click.ClickException(f"디렉토리 경로가 올바르지 않습니다: {directory_path}")
    return p

def _iter_txt_files(p: Path) -> List[Path]:
    files = sorted(p.glob("*.txt"))
    if not files:
        click.echo("분석할 .txt 파일이 디렉토리에 없습니다.")
        return []
    click.echo(f"총 {len(files)}개의 파일을 분석합니다...")
    return files

def _need_api_key():
    if not OPENAI_API_KEY:
        raise click.ClickException("OpenAI API 키가 없습니다. .env의 OPENAI_API_KEY를 설정하세요.")
    
# ---------- DB 저장 ----------
def _save_many(collection: str, docs: List[dict]) -> None:
    if not docs:
        click.echo(f"[{collection}] 저장할 문서가 없습니다.")
        return
    db = MongoDBService()
    db.insert_many_documents(collection, docs)
    db.close_connection()
    click.echo(f"[{collection}] {len(docs)}건 저장 완료.")

def save_morphemes(words: Set[str], ts: float) -> None:
    _save_many("morphemes", [{"timestamp": ts, "word": w} for w in sorted(words)])

def save_sentences(sentences: List[str], ts: float) -> None:
    _save_many("sentences", [{"timestamp": ts, "sentence": s} for s in sentences])

def save_expressions(expressions: Dict[str, List[str]], ts: float) -> None:
    docs = [
        {"timestamp": ts, "category": cat, "expression": expr}
        for cat, exprs in expressions.items()
        for expr in exprs
    ]
    _save_many("expressions", docs)

def save_parameters(parameters: Dict[str, List[str]], ts: float) -> None:
    docs = [
        {"timestamp": ts, "category": cat, "parameter": par}
        for cat, pars in parameters.items()
        for par in pars
    ]
    _save_many("parameters", docs)

def save_sentence_library(library: Dict[str, List[str]], ts: float) -> None:
    docs = [
        {"timestamp": ts, "category": cat, "sentence": sent}
        for cat, sents in library.items()
        for sent in sents
    ]
    _save_many("sentence_library", docs)

def save_manuscript(text: str, ts: float) -> None:
    _save_many("manuscripts", [{"timestamp": ts, "content": text}])

def save_subtitles(subtitles_map: Dict[str, List[str]], ts: float) -> None:
    """
    subtitles_map: { file_name: [ "부제1", "부제2", ... ] }
    """
    docs = [
        {
            "timestamp": ts,
            "subtitles": subs,
            "count": len(subs),
        }
        for fname, subs in subtitles_map.items()
    ]
    _save_many("subtitles", docs)

# ---------- 분석 단계 ----------
def run_morpheme_analysis(directory_path: str) -> Set[str]:
    p = _ensure_dir(directory_path)
    files = _iter_txt_files(p)
    all_words: Set[str] = set()
    for fp in tqdm(files, desc="형태소 분석 중", unit="파일"):
        content = fp.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue
        all_words.update(analyze_morphemes(content))
    return all_words

def run_sentence_splitting(directory_path: str) -> List[str]:
    p = _ensure_dir(directory_path)
    files = _iter_txt_files(p)
    all_sentences: List[str] = []
    for fp in tqdm(files, desc="문장 분리 중", unit="파일"):
        content = fp.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue
        all_sentences.extend(split_sentences(content))
    return all_sentences

def run_expression_extraction(directory_path: str, n: int = 2) -> Dict[str, List[str]]:
    _need_api_key()
    p = _ensure_dir(directory_path)
    files = _iter_txt_files(p)
    grouped: Dict[str, List[str]] = {}
    click.echo(f"총 {len(files)}개의 파일을 AI로 분석하여 표현을 추출합니다...")
    for fp in tqdm(files, desc="표현 추출 중", unit="파일"):
        content = fp.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue
        try:
            result = extract_expressions_with_ai(content) or {}
            for k, vals in result.items():
                grouped.setdefault(k, [])
                for v in vals:
                    if v not in grouped[k]:
                        grouped[k].append(v)
            time.sleep(API_DELAY_EXPR)
        except Exception as e:
            tqdm.write(f"-> '{fp.name}': 표현 추출 오류: {e}")
    return grouped

def run_parameters_analysis(directory_path: str) -> Dict[str, List[str]]:
    _need_api_key()
    p = _ensure_dir(directory_path)
    files = _iter_txt_files(p)
    grouped: Dict[str, List[str]] = {}
    click.echo(f"총 {len(files)}개의 파일을 AI로 분석하여 파라미터를 추출합니다...")
    for fp in tqdm(files, desc="파라미터 추출 중", unit="파일"):
        content = fp.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue
        try:
            result = extract_and_group_entities_with_ai(content) or {}
            for k, vals in result.items():
                grouped.setdefault(k, [])
                for v in vals:
                    if v not in grouped[k]:
                        grouped[k].append(v)
            time.sleep(API_DELAY_EXPR)
        except Exception as e:
            tqdm.write(f"-> '{fp.name}': 파라미터 추출 오류: {e}")
    return grouped

def run_template_generation(directory_path: str) -> List[Dict[str, str]]:
    """MongoDB 최신 parameters 사용해, 파라미터 포함 문장만 템플릿 치환."""
    p = _ensure_dir(directory_path)
    files = _iter_txt_files(p)

    db = MongoDBService()
    analysis = db.get_latest_analysis_data() or {}
    parameters: Dict[str, List[str]] = analysis.get("parameters", {})

    if not parameters:
        click.echo("추출된 파라미터가 없어 템플릿을 생성할 수 없습니다.")
        return []

    click.echo("\n추출된 파라미터 맵:")
    for k, vals in parameters.items():
        click.echo(f"- {k}: {vals}")
    click.echo("----------------------------------------")

    results: List[Dict[str, str]] = []
    for fp in tqdm(files, desc="템플릿 생성 중", unit="파일"):
        content = fp.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue

        segments: List[str] = []
        for sent in split_sentences(content):
            has_param = any(any(v in sent for v in vals) for _, vals in parameters.items())
            if not has_param:
                segments.append(sent)
                continue
            try:
                templ = generate_template_from_segment(sent, parameters)
                segments.append(templ or sent)
                time.sleep(API_DELAY_TMPL)
            except Exception as e:
                tqdm.write(f"-> '{fp.name}' 문장 '{sent[:20]}...' 템플릿 오류: {e}")
                segments.append(sent)

        results.append({"file_name": fp.name, "templated_text": " ".join(segments)})
    return results

def run_subtitle_extraction(directory_path: str, max_items: int = 12) -> Dict[str, List[str]]:
    """
    디렉토리 내 .txt 원고들에서 부제목(소제목)만 추출.
    반환: { file_name: ["부제1", "부제2", ...] }
    """
    _need_api_key()
    p = _ensure_dir(directory_path)
    files = _iter_txt_files(p)

    result: Dict[str, List[str]] = {}
    for fp in tqdm(files, desc="부제목 추출 중", unit="파일"):
        content = fp.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue
        try:
            subs = extract_subtitles_with_ai(full_text=content, max_items=max_items)
            result[fp.name] = subs or []
        except Exception as e:
            tqdm.write(f"-> '{fp.name}': 부제목 추출 오류: {e}")
            result[fp.name] = []
    return result

def save_templates_to_mongo(templates: List[Dict[str, str]]) -> None:
    if not templates:
        click.echo("저장할 템플릿이 없습니다.")
        return
    db = MongoDBService()
    now = datetime.utcnow()
    docs = [
        {"timestamp": now, "templated_text": t["templated_text"]}
        for t in templates
    ]
    db.insert_many_documents("templates", docs)
    click.echo(f"템플릿 {len(docs)}건 저장 완료.")

def run_and_save(directory_path: str) -> None:
    save_templates_to_mongo(run_template_generation(directory_path))

def run_build_library(directory_path: str):
    p = _ensure_dir(directory_path)
    return build_sentence_library(str(p))

def run_manuscript_generation(
    unique_words: List[str],
    sentences: List[str],
    expressions: Dict[str, List[str]],
    parameters: Dict[str, List[str]],
    user_instructions: str = "",
    ref: str = ""
) -> Optional[str]:
    _need_api_key()
    if not (unique_words and sentences and expressions and parameters):
        click.echo("원고 생성을 위한 데이터가 부족합니다. 먼저 분석을 실행하고 저장하세요.")
        return None
    click.echo("\n원고 생성 시작")
    try:
        return gpt_4_gen(user_instructions=user_instructions, ref=ref)
    except Exception as e:
        click.echo(f"원고 생성 오류: {e}")
        return None

# ---------- 저장 파이프라인 ----------
def save_analysis_to_mongodb(directory_path: str):
    try:
        db = MongoDBService()
        click.echo("MongoDB 연결 성공.")
        ts = time.time()

        # 1) 형태소
        click.echo("형태소 분석 → 저장 중...")
        unique_words = run_morpheme_analysis(directory_path)
        if unique_words:
            db.insert_many_documents("morphemes", [{"timestamp": ts, "word": w} for w in unique_words])
            click.echo(f"고유 단어 {len(unique_words)}개 저장 완료.")
        else:
            click.echo("저장할 고유 단어 없음.")

        # 2) 문장
        click.echo("문장 분리 → 저장 중...")
        sentences = run_sentence_splitting(directory_path)
        if sentences:
            db.insert_many_documents("sentences", [{"timestamp": ts, "sentence": s} for s in sentences])
            click.echo(f"문장 {len(sentences)}개 저장 완료.")
        else:
            click.echo("저장할 문장 없음.")

        # 3) 표현
        click.echo("표현 라이브러리 추출 → 저장 중...")
        expressions = run_expression_extraction(directory_path, n=2)
        if expressions:
            expr_docs = [
                {"timestamp": ts, "category": cat, "expression": expr}
                for cat, exprs in expressions.items()
                for expr in exprs
            ]
            db.insert_many_documents("expressions", expr_docs)
            click.echo(f"표현 {len(expr_docs)}개 저장 완료.")
        else:
            click.echo("저장할 표현 없음.")

        # 4) 파라미터
        click.echo("파라미터 추출 → 저장 중...")
        parameters = run_parameters_analysis(directory_path)
        if parameters:
            param_docs = [
                {"timestamp": ts, "category": cat, "parameter": par}
                for cat, pars in parameters.items()
                for par in pars
            ]
            db.insert_many_documents("parameters", param_docs)
            click.echo(f"파라미터 {len(param_docs)}개 저장 완료.")
        else:
            click.echo("저장할 파라미터 없음.")

        # 5) 템플릿 (생성+저장)
        click.echo("템플릿 생성 → MongoDB 저장 중...")
        run_and_save(directory_path)

        click.echo("\n모든 분석 결과가 MongoDB에 성공적으로 저장되었습니다.")

        click.echo("부제목 추출 → MongoDB 저장 중...")
        save_subtitles(run_subtitle_extraction(directory_path, max_items=12), ts)

    except Exception as e:
        click.echo(f"MongoDB 저장 중 오류: {e}")
    finally:
        try:
            if 'db' in locals() and db.client:
                db.close_connection()
                click.echo("MongoDB 연결 종료.")
        except Exception:
            pass

# ---------- 기존 메뉴형 CLI 유지 ----------
@click.command()
def cli():
    """블로그 마케팅 원고 분석 도구 (메뉴형)"""
    click.echo("수행할 작업을 선택해주세요.")

    while True:
        click.echo("\n----------------------------------------")
        click.echo("1. 형태소 분석 (morpheme)")
        click.echo("2. 문장 분리 (sentence)")
        click.echo("3. 표현 라이브러리 추출 (expression)")
        click.echo("4. 템플릿 생성 (template)")
        click.echo("5. AI 개체 인식 및 그룹화 (parameters)")
        click.echo("6. 카테고리별 문장 라이브러리 구축 (build-library)")
        click.echo("7. 원고 작성 (manuscript)")
        click.echo("8. 분석 결과 MongoDB에 저장 (save-to-mongodb)")
        click.echo("9. 부제목 추출 (subtitles)")
        click.echo("0. 종료 (exit)")
        click.echo("----------------------------------------")

        choice = click.prompt("선택 (숫자 또는 키워드)", type=str).lower()

        if choice in ('0', 'exit'):
            click.echo("도구를 종료합니다. 감사합니다!")
            break

        try:
            ts = time.time()  # ✅ 모든 명령 공통 타임스탬프

            if choice in ('1', 'morpheme'):
                directory = click.prompt("분석할 디렉토리 경로 (예: data)", type=click.Path(exists=True, file_okay=False))
                words = run_morpheme_analysis(directory)
                save_morphemes(words, ts)

            elif choice in ('2', 'sentence'):
                directory = click.prompt("분리할 디렉토리 경로 (예: data)", type=click.Path(exists=True, file_okay=False))
                sentences = run_sentence_splitting(directory)
                save_sentences(sentences, ts)

            elif choice in ('3', 'expression'):
                directory = click.prompt("추출할 디렉토리 경로 (예: data)", type=click.Path(exists=True, file_okay=False))
                n_value = click.prompt("N-gram의 N값 (기본: 2)", type=int, default=2)
                exprs = run_expression_extraction(directory, n_value)
                save_expressions(exprs, ts)

            elif choice in ('4', 'template'):
                directory = click.prompt("생성할 디렉토리 경로 (예: data)", type=click.Path(exists=True, file_okay=False))
                # 템플릿은 생성과 저장을 한 번에
                run_and_save(directory)

            elif choice in ('5', 'parameters'):
                directory = click.prompt("분석할 디렉토리 경로 (예: data)", type=click.Path(exists=True, file_okay=False))
                params = run_parameters_analysis(directory)
                save_parameters(params, ts)

            elif choice in ('6', 'build-library'):
                directory = click.prompt("구축할 디렉토리 경로 (예: data)", type=click.Path(exists=True, file_okay=False))
                lib = run_build_library(directory)
                save_sentence_library(lib, ts)

            elif choice in ('7', 'manuscript'):
                db = MongoDBService()
                analysis = db.get_latest_analysis_data() or {}
                db.close_connection()

                unique_words = analysis.get("unique_words", [])
                sentences = analysis.get("sentences", [])
                expressions = analysis.get("expressions", {})
                parameters = analysis.get("parameters", {})

                if not (unique_words and sentences and expressions and parameters):
                    click.echo("DB에 원고 생성을 위한 데이터가 부족합니다. 먼저 분석 저장을 실행하세요.")
                else:
                    user_instructions = click.prompt("원고 작성 추가 지시사항 (빈칸 가능)", type=str, default="")
                    # 간단 스피너
                    import itertools, sys, threading
                    stop = threading.Event()
                    def spinner():
                        for c in itertools.cycle("|/-\\"):
                            if stop.is_set(): break
                            sys.stdout.write(f"\rAI 원고 생성 중... {c}")
                            sys.stdout.flush()
                            time.sleep(0.1)
                        sys.stdout.write("\rAI 원고 생성 완료!     \n")
                    t = threading.Thread(target=spinner); t.start()
                    manuscript = run_manuscript_generation(
                        unique_words=list(unique_words),
                        sentences=sentences,
                        expressions=expressions,
                        parameters=parameters,
                        user_instructions=user_instructions
                    )
                    stop.set(); t.join()
                    if manuscript:
                        save_manuscript(manuscript, ts)  # ✅ 원고도 자동 저장
                        click.echo("\n" + "="*41)
                        click.echo("          ✨ 생성된 블로그 원고 ✨")
                        click.echo("="*41)
                        click.echo(manuscript)
                        click.echo("="*41)
                    else:
                        click.echo("원고 생성 실패 또는 데이터 부족.")

            elif choice in ('8', 'save-to-mongodb'):
                directory = click.prompt("MongoDB에 저장할 디렉토리 경로 (예: data)", type=click.Path(exists=True, file_okay=False))
                save_analysis_to_mongodb(directory)

            elif choice in ('9', 'subtitles'):
                directory = click.prompt("부제목을 추출할 디렉토리 경로 (예: data)", type=click.Path(exists=True, file_okay=False))
                subs_map = run_subtitle_extraction(directory, max_items=12)
                save_subtitles(subs_map, ts)  # ✅ 자동 저장
            else:
                click.echo("잘못된 선택입니다. 다시 시도해주세요.")

        except click.ClickException as ce:
            click.echo(f"[입력 오류] {ce}")
        except Exception as e:
            click.echo(f"[실행 오류] {e}")

if __name__ == '__main__':
    cli()