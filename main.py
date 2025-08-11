import click
from pathlib import Path
from tqdm import tqdm
import time # API 과호출 방지를 위한 지연 시간 추가
from collections import Counter # For expressions
from mongodb_service import MongoDBService

# --- 분석 함수들 (기존 click 명령어에서 일반 함수로 변경) ---

def run_morpheme_analysis(directory_path):
    from analyzer.morpheme import analyze_morphemes

    p = Path(directory_path)
    txt_files = list(p.glob('*.txt'))
    if not txt_files:
        click.echo("분석할 .txt 파일이 디렉토리에 없습니다.")
        return set()

    click.echo(f"총 {len(txt_files)}개의 파일을 분석합니다...")

    all_unique_words = set() # 모든 파일의 고유 단어를 저장할 set

    for file_path in tqdm(txt_files, desc="형태소 분석 중", unit="파일"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            tqdm.write(f"-> '{file_path.name}': 내용이 없어 건너뜁니다.")
            continue

        morphemes = analyze_morphemes(content) # 단어 리스트 반환
        all_unique_words.update(morphemes) # set에 단어 추가 (중복 자동 제거)
    return all_unique_words

def run_sentence_splitting(directory_path):
    from analyzer.sentence import split_sentences

    p = Path(directory_path)
    txt_files = list(p.glob('*.txt'))
    if not txt_files:
        click.echo("분석할 .txt 파일이 디렉토리에 없습니다.")
        return []

    click.echo(f"총 {len(txt_files)}개의 파일을 분석합니다...")

    all_sentences = []
    for file_path in tqdm(txt_files, desc="문장 분리 중", unit="파일"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            tqdm.write(f"-> '{file_path.name}': 내용이 없어 건너뜁니다.")
            continue

        sentence_list = split_sentences(content)
        all_sentences.extend(sentence_list)
    return all_sentences

def run_expression_extraction(directory_path, n):
    from analyzer.expression import extract_expressions_with_ai
    from config import OPENAI_API_KEY

    if not OPENAI_API_KEY:
        click.echo("오류: OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")
        return {}

    p = Path(directory_path)
    txt_files = list(p.glob('*.txt'))
    if not txt_files:
        click.echo("분석할 .txt 파일이 디렉토리에 없습니다.")
        return {}

    final_grouped_expressions = {}
    total_files = len(txt_files)

    click.echo(f"총 {total_files}개의 파일을 AI로 분석하여 표현을 추출합니다...")

    for file_path in tqdm(txt_files, desc="표현 추출 중", unit="파일"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            tqdm.write(f"-> '{file_path.name}': 내용이 없어 건너뜁니다.")
            continue

        try:
            individual_result = extract_expressions_with_ai(content)
            
            if individual_result:
                for key, values in individual_result.items():
                    if key not in final_grouped_expressions:
                        final_grouped_expressions[key] = []
                    for value in values:
                        if value not in final_grouped_expressions[key]:
                            final_grouped_expressions[key].append(value)
                tqdm.write(f"-> '{file_path.name}': 분석 및 병합 완료.")
            else:
                tqdm.write(f"-> '{file_path.name}': AI 분석에 실패했습니다.")
            
            time.sleep(1) # 1초 지연

        except Exception as e:
            tqdm.write(f"-> '{file_path.name}': 처리 중 오류 발생: {e}")

    return final_grouped_expressions


def _get_grouped_parameters_from_dir(directory_path):
    """주어진 디렉토리의 텍스트 파일들에서 AI를 이용해 개체를 추출하고 그룹화하여 반환합니다."""
    from analyzer.parameter import extract_and_group_entities_with_ai
    from config import OPENAI_API_KEY

    if not OPENAI_API_KEY:
        raise ValueError("API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")

    p = Path(directory_path)
    txt_files = list(p.glob('*.txt'))
    if not txt_files:
        click.echo("분석할 .txt 파일이 디렉토리에 없습니다.")
        return {}

    final_grouped_results = {}
    total_files = len(txt_files)

    click.echo(f"총 {total_files}개의 파일을 AI로 분석하여 파라미터를 추출합니다...")

    for file_path in tqdm(txt_files, desc="파라미터 추출 중", unit="파일"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            tqdm.write(f"-> '{file_path.name}': 내용이 없어 건너뜁니다.")
            continue

        try:
            individual_result = extract_and_group_entities_with_ai(content)
            
            if individual_result:
                for key, values in individual_result.items():
                    if key not in final_grouped_results:
                        final_grouped_results[key] = []
                    for value in values:
                        if value not in final_grouped_results[key]:
                            final_grouped_results[key].append(value)
            
            time.sleep(1) # API 과호출 방지를 위한 약간의 지연

        except Exception as e:
            tqdm.write(f"-> '{file_path.name}': 파라미터 추출 중 오류 발생: {e}")

    return final_grouped_results

def run_template_generation(directory_path):
    from analyzer.template import generate_template_from_segment
    from analyzer.sentence import split_sentences # 문장 분리 함수 임포트

    # 1. 파라미터 추출을 위한 디렉토리 경로 입력받기
    param_dir = click.prompt("파라미터를 추출할 디렉토리 경로를 입력하세요 (예: data)", type=click.Path(exists=True, file_okay=False))
    known_parameters_map = _get_grouped_parameters_from_dir(param_dir)

    if not known_parameters_map:
        click.echo("추출된 파라미터가 없어 템플릿을 생성할 수 없습니다.")
        return []

    click.echo("\n추출된 파라미터 맵:")
    for key, values in known_parameters_map.items():
        click.echo(f"- {key}: {values}")
    click.echo("----------------------------------------")

    # 2. 템플릿을 생성할 원고 디렉토리 분석
    p = Path(directory_path)
    txt_files = list(p.glob('*.txt'))
    if not txt_files:
        click.echo("분석할 .txt 파일이 디렉토리에 없습니다.")
        return []

    click.echo(f"총 {len(txt_files)}개의 파일을 분석하여 템플릿을 생성합니다...")

    all_templated_texts = []
    for file_path in tqdm(txt_files, desc="템플릿 생성 중", unit="파일"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            tqdm.write(f"-> '{file_path.name}': 내용이 없어 건너뜁니다.")
            continue

        # 원고를 문장 단위로 분리
        sentences = split_sentences(content)
        templated_segments = []

        for sentence in sentences:
            # 문장 내에 known_parameters_map의 어떤 값이라도 포함되어 있는지 확인
            has_param_value = False
            for key, values in known_parameters_map.items():
                for value in values:
                    if value in sentence:
                        has_param_value = True
                        break
                if has_param_value:
                    break
            
            if has_param_value:
                # 파라미터가 포함된 문장만 AI에 요청
                try:
                    templated_segment = generate_template_from_segment(sentence, known_parameters_map)
                    if templated_segment:
                        templated_segments.append(templated_segment)
                        time.sleep(0.5) # API 과호출 방지를 위한 약간의 지연
                    else:
                        templated_segments.append(sentence) # AI 실패 시 원본 유지
                except Exception as e:
                    tqdm.write(f"-> '{file_path.name}' 문장 '{sentence[:20]}...' 템플릿 생성 중 오류: {e}")
                    templated_segments.append(sentence) # 오류 발생 시 원본 유지
            else:
                templated_segments.append(sentence) # 파라미터 없는 문장은 그대로 유지
        
        final_templated_text = ' '.join(templated_segments) # 문장들을 다시 합침
        all_templated_texts.append({"file_name": file_path.name, "templated_text": final_templated_text})
    return all_templated_texts



def run_parameters_analysis(directory_path):
    from analyzer.parameter import extract_and_group_entities_with_ai
    from config import OPENAI_API_KEY

    if not OPENAI_API_KEY:
        click.echo("오류: OpenAI API 키가 설정되지 않았습니다. .env 파일을 생성하고 OPENAI_API_KEY를 입력해주세요.")
        return {}

    p = Path(directory_path)
    txt_files = list(p.glob('*.txt'))
    if not txt_files:
        click.echo("분석할 .txt 파일이 디렉토리에 없습니다.")
        return {}

    final_grouped_results = {}
    total_files = len(txt_files)

    click.echo(f"총 {total_files}개의 파일을 분석합니다...")

    for file_path in tqdm(txt_files, desc="파일 분석 중", unit="파일"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            tqdm.write(f"-> '{file_path.name}': 내용이 없어 건너뜁니다.")
            continue

        try:
            individual_result = extract_and_group_entities_with_ai(content)
            
            if individual_result:
                for key, values in individual_result.items():
                    if key not in final_grouped_results:
                        final_grouped_results[key] = []
                    for value in values:
                        if value not in final_grouped_results[key]:
                            final_grouped_results[key].append(value)
                tqdm.write(f"-> '{file_path.name}': 분석 및 병합 완료.")
            else:
                tqdm.write(f"-> '{file_path.name}': AI 분석에 실패했습니다.")
            
            time.sleep(1) # 1초 지연

        except Exception as e:
            tqdm.write(f"-> '{file_path.name}': 처리 중 오류 발생: {e}")

    return final_grouped_results

def run_build_library(directory_path):
    from analyzer.library import build_sentence_library
    
    library = build_sentence_library(directory_path)
    return library

def _get_unique_words_from_dir(directory_path):
    from analyzer.morpheme import analyze_morphemes
    p = Path(directory_path)
    txt_files = list(p.glob('*.txt'))
    if not txt_files:
        return set()
    all_unique_words = set()
    for file_path in txt_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if content.strip():
            morphemes = analyze_morphemes(content)
            all_unique_words.update(morphemes)
    return all_unique_words

def _get_sentences_from_dir(directory_path):
    from analyzer.sentence import split_sentences
    p = Path(directory_path)
    txt_files = list(p.glob('*.txt'))
    if not txt_files:
        return []
    all_sentences = []
    for file_path in txt_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if content.strip():
            all_sentences.extend(split_sentences(content))
    return all_sentences

def _get_expressions_from_dir(directory_path, n):
    from analyzer.expression import extract_expressions_with_ai
    from config import OPENAI_API_KEY

    if not OPENAI_API_KEY:
        raise ValueError("API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")

    p = Path(directory_path)
    txt_files = list(p.glob('*.txt'))
    if not txt_files:
        return {}

    final_grouped_expressions = {}
    for file_path in txt_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if content.strip():
            try:
                individual_result = extract_expressions_with_ai(content)
                if individual_result:
                    for key, values in individual_result.items():
                        if key not in final_grouped_expressions:
                            final_grouped_expressions[key] = []
                        for value in values:
                            if value not in final_grouped_expressions[key]:
                                final_grouped_expressions[key].append(value)
                time.sleep(1)
            except Exception as e:
                print(f"표현 추출 중 오류 발생: {e}")
    return final_grouped_expressions

def run_manuscript_generation(unique_words: list, sentences: list, expressions: dict, parameters: dict, user_instructions: str = "", ref=''):
    from analyzer.manuscript_generator import generate_manuscript_with_ai
    from config import OPENAI_API_KEY

    if not OPENAI_API_KEY:
        click.echo("오류: OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")
        return None

    if not (unique_words and sentences and expressions and parameters):
        click.echo("원고 생성을 위한 분석 데이터(고유 단어, 문장, 표현, 파라미터)가 부족합니다. MongoDB에 데이터가 있는지 확인하거나 먼저 분석을 실행하고 저장해주세요.")
        return None

    click.echo("\n--- AI 원고 생성 시작 ---")

    try:
        generated_manuscript = generate_manuscript_with_ai(
            unique_words=unique_words,
            sentences=sentences,
            expressions=expressions,
            parameters=parameters,
            user_instructions=user_instructions,
            ref=ref
        )
        return generated_manuscript

    except Exception as e:
        click.echo(f"원고 생성 중 오류 발생: {e}")
        return None


def save_analysis_to_mongodb(directory_path):
    try:
        db_service = MongoDBService()
        click.echo("MongoDB 연결 성공.")
        current_time = time.time()

        # 1. 형태소 분석 결과 저장
        click.echo("형태소 분석 결과를 MongoDB에 저장 중...")
        unique_words = run_morpheme_analysis(directory_path)
        if unique_words:
            word_documents = [{"timestamp": current_time, "word": word} for word in unique_words]
            db_service.insert_many_documents("morphemes", word_documents)
            click.echo(f"고유 단어 {len(unique_words)}개 저장 완료.")
        else:
            click.echo("저장할 고유 단어가 없습니다.")

        # 2. 문장 분리 결과 저장
        click.echo("문장 분리 결과를 MongoDB에 저장 중...")
        sentences = run_sentence_splitting(directory_path)
        if sentences:
            sentence_documents = [{"timestamp": current_time, "sentence": sentence} for sentence in sentences]
            db_service.insert_many_documents("sentences", sentence_documents)
            click.echo(f"문장 {len(sentences)}개 저장 완료.")
        else:
            click.echo("저장할 문장이 없습니다.")

        # 3. 표현 라이브러리 추출 결과 저장
        click.echo("표현 라이브러리 추출 결과를 MongoDB에 저장 중...")
        expressions = run_expression_extraction(directory_path, n=2)
        if expressions:
            expression_documents = []
            for category, expr_list in expressions.items():
                for expr in expr_list:
                    expression_documents.append({"timestamp": current_time, "category": category, "expression": expr})
            db_service.insert_many_documents("expressions", expression_documents)
            click.echo(f"표현 그룹 {len(expression_documents)}개 저장 완료.")
        else:
            click.echo("저장할 표현이 없습니다.")

        # 4. 파라미터 추출 결과 저장
        click.echo("파라미터 추출 결과를 MongoDB에 저장 중...")
        parameters = run_parameters_analysis(directory_path)
        if parameters:
            parameter_documents = []
            for category, param_list in parameters.items():
                for param in param_list:
                    parameter_documents.append({"timestamp": current_time, "category": category, "parameter": param})
            db_service.insert_many_documents("parameters", parameter_documents)
            click.echo(f"파라미터 그룹 {len(parameter_documents)}개 저장 완료.")
        else:
            click.echo("저장할 파라미터가 없습니다.")

        # 5. 원고 생성 결과 저장 (선택 사항)
        generate_manuscript = click.confirm("원고 생성 결과를 MongoDB에 저장하시겠습니까? (AI 호출 필요)", default=False)
        if generate_manuscript:
            click.echo("원고 생성 중...")
            user_instructions = click.prompt("원고 작성에 대한 추가 지시사항을 입력하세요 (예: '친근한 어조로 작성하고, 마지막에 구매 유도 문구를 넣어주세요.')", type=str, default="")
            manuscript = run_manuscript_generation(unique_words=list(unique_words), sentences=sentences, expressions=expressions, parameters=parameters, user_instructions=user_instructions)
            if manuscript:
                db_service.insert_document("manuscripts", {"timestamp": current_time, "content": manuscript})
                click.echo("원고 저장 완료.")
                click.echo("\n=========================================")
                click.echo("          ✨ 생성된 블로그 원고 ✨")
                click.echo("=========================================")
                click.echo(manuscript)
                click.echo("=========================================")
            else:
                click.echo("원고 생성 및 저장 실패.")
        
        click.echo("\n모든 분석 결과가 MongoDB에 성공적으로 저장되었습니다.")

    except Exception as e:
        click.echo(f"MongoDB 저장 중 오류 발생: {e}")
    finally:
        if 'db_service' in locals() and db_service.client:
            db_service.close_connection()
            click.echo("MongoDB 연결 종료.")

# --- 메인 CLI 진입점 (대화형) ---
@click.command()
def cli():
    """블로그 마케팅 원고 분석 도구"""
    click.echo("\n✨ 블로그 원고 분석 도구에 오신 것을 환영합니다! ✨")
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
        click.echo("0. 종료 (exit)")
        click.echo("----------------------------------------")

        choice = click.prompt("선택 (숫자 또는 키워드)", type=str).lower()

        if choice in ('0', 'exit'):
            click.echo("도구를 종료합니다. 감사합니다!")
            break

        elif choice in ('1', 'morpheme'):
            directory = click.prompt("분석할 디렉토리 경로를 입력하세요 (예: data)", type=click.Path(exists=True, file_okay=False))
            run_morpheme_analysis(directory)

        elif choice in ('2', 'sentence'):
            directory = click.prompt("분리할 디렉토리 경로를 입력하세요 (예: data)", type=click.Path(exists=True, file_okay=False))
            run_sentence_splitting(directory)

        elif choice in ('3', 'expression'):
            directory = click.prompt("추출할 디렉토리 경로를 입력하세요 (예: data)", type=click.Path(exists=True, file_okay=False))
            n_value = click.prompt("N-gram의 N값을 입력하세요 (기본값: 2)", type=int, default=2)
            run_expression_extraction(directory, n_value)

        elif choice in ('4', 'template'):
            directory = click.prompt("생성할 디렉토리 경로를 입력하세요 (예: data)", type=click.Path(exists=True, file_okay=False))
            run_template_generation(directory)

        elif choice in ('5', 'parameters'):
            directory = click.prompt("분석할 디렉토리 경로를 입력하세요 (예: data)", type=click.Path(exists=True, file_okay=False))
            run_parameters_analysis(directory)

        elif choice in ('6', 'build-library'):
            directory = click.prompt("구축할 디렉토리 경로를 입력하세요 (예: data)", type=click.Path(exists=True, file_okay=False))
            run_build_library(directory)

        elif choice in ('7', 'manuscript'):
            db_service = None
            try:
                db_service = MongoDBService()
                analysis_data = db_service.get_latest_analysis_data()

                unique_words = analysis_data.get("unique_words", [])
                sentences = analysis_data.get("sentences", [])
                expressions = analysis_data.get("expressions", {})
                parameters = analysis_data.get("parameters", {})

                def spinner(stop_event):
                    import itertools
                    import sys
                    
                    for cursor in itertools.cycle('|/-\\'):
                        if stop_event.is_set():
                            break
                        sys.stdout.write(f'\rAI 원고 생성 중... {cursor}')
                        sys.stdout.flush()
                        time.sleep(0.1)
                    sys.stdout.write('\rAI 원고 생성 완료!     \n')
                    
                if not (unique_words and sentences and expressions and parameters):
                    click.echo("MongoDB에 원고 생성을 위한 충분한 분석 데이터가 없습니다. 먼저 분석을 실행하고 저장해주세요.")
                else:
                    user_instructions = click.prompt("원고 작성에 대한 추가 지시사항을 입력하세요 (예: '친근한 어조로 작성하고, 마지막에 구매 유도 문구를 넣어주세요.')", type=str, default="")
                    import threading
                    stop_event = threading.Event()
                    t = threading.Thread(target=spinner, args=(stop_event,))
                    t.start()
                    generated_manuscript = run_manuscript_generation(
                        unique_words=unique_words,
                        sentences=sentences,
                        expressions=expressions,
                        parameters=parameters,
                        user_instructions=user_instructions
                    )

                    stop_event.set()
                    t.join()    
                    if generated_manuscript:
                        click.echo("\n=========================================")
                        click.echo("          ✨ 생성된 블로그 원고 ✨")
                        click.echo("=========================================")
                        click.echo(generated_manuscript)
                        click.echo("=========================================")
                    else:
                        stop_event.set()
                        t.join()    
                        click.echo("원고 생성에 실패했습니다.")
            except Exception as e:
                click.echo(f"원고 생성 중 오류 발생: {e}")
            finally:
                if db_service:
                    db_service.close_connection()

        elif choice in ('8', 'save-to-mongodb'):
            directory = click.prompt("MongoDB에 저장할 분석 데이터가 있는 디렉토리 경로를 입력하세요 (예: data)", type=click.Path(exists=True, file_okay=False))
            save_analysis_to_mongodb(directory)

        else:
            click.echo("잘못된 선택입니다. 다시 시도해주세요.")

if __name__ == '__main__':
    cli()