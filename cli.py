import os
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional

import click
from tqdm import tqdm

from analyzer.morpheme import analyze_morphemes
from analyzer.sentence import split_sentences
from analyzer.expression import gen_expressions
from analyzer.parameter import parameter_gen
from analyzer.template import (
    template_gen,
)
from analyzer.library import build_sentence_library
from llm.gpt_4_service import gpt_4_gen
from analyzer.subtitle import gen_subtitles
from config import OPENAI_API_KEY


API_DELAY_EXPR = 1.0


def _ensure_dir(directory_path: str) -> Path:
    p = Path(directory_path)
    if not p.exists() or not p.is_dir():
        raise click.ClickException(
            f"디렉토리 경로가 올바르지 않습니다: {directory_path}"
        )
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
        raise click.ClickException(
            "OpenAI API 키가 없습니다. .env의 OPENAI_API_KEY를 설정하세요."
        )


# DB 저장 함수들 제거됨 - 이제 각 analyzer 모듈에서 직접 처리


def run_morpheme_analysis(directory_path: str, category: str = "") -> Set[str]:
    p = _ensure_dir(directory_path)
    files = _iter_txt_files(p)
    category = directory_path.replace("_docs/", "", 1)

    all_words: Set[str] = set()
    for fp in tqdm(files, desc="형태소 분석 중", unit="파일"):
        content = fp.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue
        words = analyze_morphemes(content, category, fp.name)
        all_words.update(words)
    return all_words


def run_sentence_splitting(directory_path: str, category: str = "") -> List[str]:
    p = _ensure_dir(directory_path)
    files = _iter_txt_files(p)
    all_sentences: List[str] = []
    category = directory_path.replace("_docs/", "", 1)

    for fp in tqdm(files, desc="문장 분리 중", unit="파일"):
        content = fp.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue
        sentences = split_sentences(content, category, fp.name)
        all_sentences.extend(sentences)
    return all_sentences


def run_expression_extraction(
    directory_path: str, category: str = "", n: int = 2
) -> Dict[str, List[str]]:
    _need_api_key()
    p = _ensure_dir(directory_path)
    files = _iter_txt_files(p)
    category = directory_path.replace("_docs/", "", 1)

    grouped: Dict[str, List[str]] = {}
    click.echo(f"총 {len(files)}개의 파일을 AI로 분석하여 표현을 추출합니다...")
    for fp in tqdm(files, desc="표현 추출 중", unit="파일"):
        content = fp.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue
        try:
            result = gen_expressions(content, category, fp.name) or {}
            for k, vals in result.items():
                grouped.setdefault(k, [])
                for v in vals:
                    if v not in grouped[k]:
                        grouped[k].append(v)
            time.sleep(API_DELAY_EXPR)
        except Exception as e:
            tqdm.write(f"-> '{fp.name}': 표현 추출 오류: {e}")
    return grouped


def run_parameters_analysis(
    directory_path: str, category: str = ""
) -> Dict[str, List[str]]:
    _need_api_key()
    p = _ensure_dir(directory_path)
    files = _iter_txt_files(p)
    category = directory_path.replace("_docs/", "", 1)

    grouped: Dict[str, List[str]] = {}
    click.echo(f"총 {len(files)}개의 파일을 AI로 분석하여 파라미터를 추출합니다...")
    for fp in tqdm(files, desc="파라미터 추출 중", unit="파일"):
        docs = fp.read_text(encoding="utf-8", errors="ignore")
        if not docs.strip():
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue
        try:
            result = parameter_gen(docs, category, fp.name) or {}
            for k, vals in result.items():
                grouped.setdefault(k, [])
                for v in vals:
                    if v not in grouped[k]:
                        grouped[k].append(v)
            time.sleep(API_DELAY_EXPR)
        except Exception as e:
            tqdm.write(f"-> '{fp.name}': 파라미터 추출 오류: {e}")
    return grouped


def run_template_generation(
    directory_path: str,
    custom_instruction: Optional[str] = None,
) -> List[Dict[str, str]]:
    p = Path(directory_path)
    files = list(p.glob("*.txt"))
    category = directory_path.replace("_docs/", "", 1)
    if not files:
        click.echo("⚠️ 텍스트 파일이 없습니다.")
        return []

    if custom_instruction is None:
        custom_instruction = click.prompt(
            "GPT-5에 전달할 사용자 지시(엔터로 건너뜀)",
            default="",
            show_default=False,
        )

    results: List[Dict[str, str]] = []

    for fp in tqdm(files, desc="템플릿 생성 중", unit="파일"):
        content = fp.read_text(encoding="utf-8", errors="ignore").strip()

        if not content:
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue

        user_instructions = f"{custom_instruction}".strip()

        try:
            templated_text = template_gen(
                user_instructions=user_instructions,
                docs=content,
                category=category,
                file_name=fp.name,
            )
            results.append(
                {
                    "file_name": fp.name,
                    "templated_text": templated_text,
                }
            )
        except Exception as e:
            tqdm.write(f"-> '{fp.name}': 처리 실패 ({e})")

    click.echo("✅ GPT-5 템플릿 생성 완료")
    return results


def run_subtitle_extraction(
    directory_path: str, category: str = ""
) -> Dict[str, List[str]]:
    """
    디렉토리 내 .txt 원고들에서 부제목(소제목)만 추출.
    반환: { file_name: ["부제1", "부제2", ...] }
    """
    _need_api_key()
    p = _ensure_dir(directory_path)
    files = _iter_txt_files(p)
    category = directory_path.replace("_docs/", "", 1)

    result: Dict[str, List[str]] = {}
    for fp in tqdm(files, desc="부제목 추출 중", unit="파일"):
        content = fp.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            tqdm.write(f"-> '{fp.name}': 내용 없음, 건너뜀")
            continue
        try:
            subs = gen_subtitles(
                full_text=content, category=category, file_name=fp.name
            )
            result[fp.name] = subs or []
        except Exception as e:
            tqdm.write(f"-> '{fp.name}': 부제목 추출 오류: {e}")
            result[fp.name] = []
    return result


def run_build_library(directory_path: str):
    p = _ensure_dir(directory_path)
    return build_sentence_library(str(p))


def run_manuscript_generation(
    unique_words: List[str],
    sentences: List[str],
    expressions: Dict[str, List[str]],
    parameters: Dict[str, List[str]],
    user_instructions: str = "",
    ref: str = "",
) -> Optional[str]:
    _need_api_key()
    if not (unique_words and sentences and expressions and parameters):
        click.echo(
            "원고 생성을 위한 데이터가 부족합니다. 먼저 분석을 실행하고 저장하세요."
        )
        return None
    click.echo("\n원고 생성 시작")
    try:
        return gpt_4_gen(user_instructions=user_instructions, ref=ref)
    except Exception as e:
        click.echo(f"원고 생성 오류: {e}")
        return None


def save_analysis_to_mongodb(directory_path: str):
    """분석 결과를 MongoDB에 저장 - 이제 각 analyzer가 자동으로 처리"""
    try:
        category = directory_path.replace("_data/", "").replace("/", "_")
        click.echo(f"{category} 카테고리로 분석을 시작합니다.")

        click.echo("형태소 분석 → 저장 중...")
        unique_words = run_morpheme_analysis(directory_path, category)
        click.echo(f"고유 단어 {len(unique_words) if unique_words else 0}개 처리 완료.")

        click.echo("문장 분리 → 저장 중...")
        sentences = run_sentence_splitting(directory_path, category)
        click.echo(f"문장 {len(sentences) if sentences else 0}개 처리 완료.")

        click.echo("표현 라이브러리 추출 → 저장 중...")
        expressions = run_expression_extraction(directory_path, category, n=2)
        total_expressions = (
            sum(len(exprs) for exprs in expressions.values()) if expressions else 0
        )
        click.echo(f"표현 {total_expressions}개 처리 완료.")

        click.echo("파라미터 추출 → 저장 중...")
        parameters = run_parameters_analysis(directory_path, category)
        total_params = (
            sum(len(pars) for pars in parameters.values()) if parameters else 0
        )
        click.echo(f"파라미터 {total_params}개 처리 완료.")

        click.echo("부제목 추출 → 저장 중...")
        subtitles_result = run_subtitle_extraction(directory_path, category)
        total_subtitles = (
            sum(len(subs) for subs in subtitles_result.values())
            if subtitles_result
            else 0
        )
        click.echo(f"부제목 {total_subtitles}개 처리 완료.")

        click.echo("템플릿 추출 → 저장 중...")
        run_template_generation(directory_path, category)

        click.echo(f"템플릿 처리 완료.")

        click.echo("\n모든 분석 결과가 MongoDB에 성공적으로 저장되었습니다.")

    except Exception as e:
        click.echo(f"분석 중 오류: {e}")


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

        if choice in ("0", "exit"):
            click.echo("도구를 종료합니다. 감사합니다!")
            break

        try:
            ts = time.time()

            if choice in ("1", "morpheme"):
                directory = click.prompt(
                    "분석할 디렉토리 경로 (예: data)",
                    type=click.Path(exists=True, file_okay=False),
                )
                words = run_morpheme_analysis(directory)
                click.echo(f"형태소 {len(words)}개 추출 완료!")

            elif choice in ("2", "sentence"):
                directory = click.prompt(
                    "분리할 디렉토리 경로 (예: data)",
                    type=click.Path(exists=True, file_okay=False),
                )
                sentences = run_sentence_splitting(directory)
                click.echo(f"문장 {len(sentences)}개 분리 완료!")

            elif choice in ("3", "expression"):
                directory = click.prompt(
                    "추출할 디렉토리 경로 (예: data)",
                    type=click.Path(exists=True, file_okay=False),
                )
                n_value = click.prompt("N-gram의 N값 (기본: 2)", type=int, default=2)
                exprs = run_expression_extraction(directory, "", n_value)
                total_exprs = sum(len(v) for v in exprs.values())
                click.echo(f"표현 {total_exprs}개 추출 완료!")

            elif choice in ("4", "template"):
                directory = click.prompt(
                    "생성할 디렉토리 경로 (예: data)",
                    type=click.Path(exists=True, file_okay=False),
                )

                run_template_generation(directory)

            elif choice in ("5", "parameters"):
                directory = click.prompt(
                    "분석할 디렉토리 경로 (예: data)",
                    type=click.Path(exists=True, file_okay=False),
                )
                params = run_parameters_analysis(directory)
                total_params = sum(len(v) for v in params.values())
                click.echo(f"파라미터 {total_params}개 추출 완료!")

            elif choice in ("6", "build-library"):
                directory = click.prompt(
                    "구축할 디렉토리 경로 (예: data)",
                    type=click.Path(exists=True, file_okay=False),
                )
                lib = run_build_library(directory)
                total_sentences = sum(len(v) for v in lib.values())
                click.echo(f"라이브러리 {total_sentences}개 문장 구축 완료!")

            elif choice in ("7", "manuscript"):
                # TODO: MongoDB에서 분석 데이터를 조회하는 기능 재구현 필요
                click.echo("원고 생성 기능은 현재 리팩토링 중입니다.")

            elif choice in ("8", "save-to-mongodb"):
                directory = click.prompt(
                    "MongoDB에 저장할 디렉토리 경로 (예: data)",
                    type=click.Path(exists=True, file_okay=False),
                )
                save_analysis_to_mongodb(directory)

            elif choice in ("9", "subtitles"):
                directory = click.prompt(
                    "부제목을 추출할 디렉토리 경로 (예: data)",
                    type=click.Path(exists=True, file_okay=False),
                )
                subs_map = run_subtitle_extraction(directory)
                total_subs = sum(len(v) for v in subs_map.values())
                click.echo(f"부제목 {total_subs}개 추출 완료!")
            else:
                click.echo("잘못된 선택입니다. 다시 시도해주세요.")

        except click.ClickException as ce:
            click.echo(f"[입력 오류] {ce}")
        except Exception as e:
            click.echo(f"[실행 오류] {e}")


if __name__ == "__main__":
    cli()
