from __future__ import annotations
import re
import time

from openai import OpenAI
from _prompts.category import 알파CD
from _prompts.service.get_mongo_prompt import get_mongo_prompt
from config import GEMINI_API_KEY, OPENAI_API_KEY
from _constants.Model import Model
from _prompts.service.get_ref_prompt import get_ref_prompt
from utils.format_paragraphs import format_paragraphs
from utils.query_parser import parse_query
from utils.text_cleaner import comprehensive_text_clean

from google import genai
from google.genai import types

from _prompts.category.맛집 import 맛집
from _prompts.category.애견동물_반려동물_분양 import 애견동물_반려동물_분양
from _prompts.category.공항_장기주차장_주차대행 import 공항_장기주차장_주차대행
from _prompts.category.미용학원 import 미용학원
from _prompts.category.다이어트 import 다이어트
from _prompts.category.멜라논크림 import 멜라논크림
from _prompts.category.위고비 import 위고비

from _prompts.category.anime import anime
from _prompts.category.movie import movie
from _prompts.category.wedding import wedding
from _prompts.category.캐리어 import 캐리어
from _prompts.category.기타 import 기타
from _prompts.category.라미네이트 import 라미네이트
from _prompts.category.리쥬란 import 리쥬란
from _prompts.category.리들샷 import 리들샷
from _prompts.category.서브웨이다이어트 import 서브웨이다이어트
from _prompts.category.에리스리톨 import 에리스리톨
from _prompts.category.외국어교육 import 외국어교육
from _prompts.category.외국어교육_학원 import 외국어교육_학원
from _prompts.category.울쎄라 import 울쎄라
from _prompts.category.족저근막염깔창 import 족저근막염깔창
from _prompts.category.텔레그램사기 import 텔레그램사기
from _prompts.category.틱톡부업사기 import 틱톡부업사기

from _prompts.category.beauty_treatment import beauty_treatment

from _prompts.rules.anti_ai_writing_patterns import anti_ai_writing_patterns
from _prompts.rules.human_writing_style import human_writing_style
from _prompts.rules.line_example_rule import line_example_rule
from _prompts.rules.line_break_rules import line_break_rules


model_name: str = Model.GPT5


ai_service_type = "gemini" if model_name.startswith("gemini") else "openai"


openai_client = OpenAI(api_key=OPENAI_API_KEY) if ai_service_type == "openai" else None
gemini_client = (
    genai.Client(api_key=GEMINI_API_KEY) if ai_service_type == "gemini" else None
)


def kkk_gen(user_instructions: str, ref: str = "", category: str = "") -> str:
    if ai_service_type == "gemini" and not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")
    elif ai_service_type == "openai" and not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env를 확인하세요.")

    parsed = parse_query(user_instructions)
    keyword, note = parsed.get("keyword", ""), parsed.get("note", "")

    if not keyword:
        raise ValueError("키워드가 없습니다.")
    if model_name == Model.GPT5_CHAT:
        target_chars_min, target_chars_max = 3000, 3200
    if model_name == Model.GPT4_1:
        target_chars_min, target_chars_max = 2400, 2600
    else:
        target_chars_min, target_chars_max = 2000, 2300

    mongo_data = get_mongo_prompt(category, user_instructions)
    category_tone_rules = get_category_tone_rules(category)
    ref_prompt = get_ref_prompt(ref)
    system = f"""
    <self_reflection>
        <quality_criteria priority="ordered">
            <criterion id="1" importance="critical">
                <name>SEO 키워드 최적화</name>
                <check>자연스러운 키워드 통합 여부</check>
                <target>3-5% 밀도, 제목/소제목 포함</target>
            </criterion>
            
            <criterion id="2" importance="critical">
                <name>독자 참여도</name>
                <check>가독성과 톤의 적절성</check>
                <target>체류시간 3분 이상 유도</target>
            </criterion>
            
            <criterion id="3" importance="high">
                <name>구조적 완성도</name>
                <check>자연스러운 흐름 (도입-전개-마무리)</check>
                <target>라벨 없이 유기적 연결</target>
            </criterion>
            
            <criterion id="4" importance="high">
                <name>길이 요구사항</name>
                <check>{target_chars_min}-{target_chars_max}자 준수</check>
                <target>정확한 글자 수 충족</target>
            </criterion>
            
            <criterion id="5" importance="medium">
                <name>카테고리별 톤</name>
                <check>카테고리 특성에 맞는 어투</check>
                <target>타겟 독자층 공감</target>
            </criterion>
            
            <criterion id="6" importance="critical">
                <name>인간다운 자연스러움</name>
                <check>AI 티 나지 않는 문체</check>
                <target>실제 블로거의 글처럼</target>
            </criterion>
        </quality_criteria>
    </self_reflection>

    <task_definition>
    네이버 블로그 SEO 최적화 글 작성
    - 핵심 키워드: {keyword}
    - 카테고리: {category}
    - 목표 길이: {target_chars_min}-{target_chars_max}자
    </task_definition>

    <output_structure>
        <format>
            <structure>
                제목 (20-35자, 키워드 포함)

                제목
                제목
                제목
                
                도입부 (3-5줄, 라벨 없이 자연스럽게)
                
                1. 첫 번째 소제목
                본문 (200-300자)
                
                2. 두 번째 소제목
                본문 (300-400자)
                
                3. 세 번째 소제목
                본문 (500-600자)
                
                4. 네 번째 소제목
                본문 (500-600자)
                
                5. 다섯 번째 소제목
                본문 (250-300자)
                
                맺음말 (2-3문장, 라벨 없이 자연스럽게)

                --- (여기서만 마크다운 허용)

                지침 사항에 대한 상세한 피드백

            </structure>
            
            <important_notes>
                - "서론", "마무리" 등의 라벨 절대 사용 금지
                - 자연스러운 흐름으로 시작과 끝 처리
                - 각 섹션은 충분한 줄바꿈으로만 구분
                - 제목에는 쉼표(,) 금지
                = QnA 금지
            </important_notes>
        </format>
        <restrictions>
            <forbidden_expressions priority="critical">
                <meta_expressions>
                    <item>요약하자면</item>
                    <item>결론적으로</item>
                    <item>마무리하자면</item>
                    <item>정리하면</item>
                    <item>다시 말해</item>
                    <item>이미지 힌트 가격 범위 인포그래픽</item>
                </meta_expressions>
                <structural_labels>
                    <item>서론</item>
                    <item>본론</item>
                    <item>결론</item>
                    <item>마무리</item>
                    <item>들어가며</item>
                    <item>끝으로</item>
                </structural_labels>
            </forbidden_expressions>
            
            <forbidden_formatting priority="critical">
                <markdown_syntax>
                    <item># (헤딩)</item>
                    <item>* (리스트)</item>
                    <item>- (대시)</item>
                    <item>[]() (링크)</item>
                    <item>``` (코드블록)</item>
                    <item>** (볼드)</item>
                    <item>__ (언더라인)</item>
                    <item>~~ (취소선)</item>
                </markdown_syntax>
                <html_tags>
                    <item>&lt;p&gt;</item>
                    <item>&lt;br&gt;</item>
                    <item>&lt;div&gt;</item>
                    <item>&lt;span&gt;</item>
                    <item>&lt;a&gt;</item>
                    <item>&lt;img&gt;</item>
                    <item>&lt;h1-h6&gt;</item>
                    <item>&lt;table&gt;</item>
                </html_tags>
                <urls>
                    <item>http://</item>
                    <item>https://</item>
                    <item>www.</item>
                    <item>.com</item>
                    <item>.co.kr</item>
                </urls>
            </forbidden_formatting>
            
            <forbidden_characters priority="high">
                <quotes>
                    <item>" (큰따옴표)</item>
                    <item>' (작은따옴표)</item>
                    <item>` (백틱)</item>
                    <item>' (좌측 따옴표)</item>
                    <item>' (우측 따옴표)</item>
                    <item>" (좌측 큰따옴표)</item>
                    <item>" (우측 큰따옴표)</item>
                </quotes>
                <special_chars>
                    <item>· (가운뎃점)</item>
                    <item>• (불릿)</item>
                    <item>◦ (빈 원)</item>
                    <item>▪ (사각형)</item>
                    <item>→ (화살표)</item>
                    <item>※ (참고표시)</item>
                </special_chars>
                <brackets>
                    <item>[] (대괄호)</item>
                    <item>&lt;&gt; (꺾쇠괄호)</item>
                    <item>{{}} (중괄호)</item>
                    <item>⟨⟩ (각괄호)</item>
                    <item>【】(겹꺾쇠)</item>
                </brackets>
            </forbidden_characters>
            
            <allowed_alternatives>
                <for_emphasis>
                    <allowed>느낌표(!), 물음표(?)</allowed>
                    <allowed>ㅎㅎ, ㅋㅋ, ㅜㅜ 등 감정표현</allowed>
                    <allowed>자연스러운 이모지</allowed>
                </for_emphasis>
                <for_structure>
                    <allowed>숫자 넘버링 (1. 2. 3.)</allowed>
                    <allowed>부제 하단은 두번의 줄바꿈</allowed>
                    <allowed>자연스러운 단락 구분</allowed>
                    <allowed>충분한 줄바꿈으로 구분</allowed>
                </for_structure>
                <for_quotes>
                    <allowed>간접 인용으로 표현</allowed>
                    <allowed>~라고/다고 형식 사용</allowed>
                </for_quotes>
            </allowed_alternatives>
            
            <enforcement_level>
                <strict>formatting, characters, brackets</strict>
                <moderate>expressions (문맥상 필요시 유연하게)</moderate>
            </enforcement_level>

        </restrictions>
        <rule>가독성을 위해 약 40자마다 자연스러운 줄바꿈</rule>
        {line_break_rules}
    </output_structure>

    {human_writing_style}

    <tone_control category="{category}">
    {category_tone_rules}
    </tone_control>

    <seo_optimization>
        <keyword_strategy>
            <rule_1>제목에 핵심 키워드 필수 포함</rule_1>
            <rule_2>본문 키워드 밀도: 3-5%</rule_2>
            <rule_3>연관 키워드 자연스럽게 분산</rule_3>
        </keyword_strategy>
        <content_quality>
            - 유용한 정보 제공 우선
            - 독자 체류시간 증대 위한 흥미로운 구성
            - 자연스러운 내부 링크 언급 가능
        </content_quality>
    </seo_optimization>

    <length_constraints>
        <total_length min={target_chars_min} max={target_chars_max} unit="chars_no_space"/>
        <distribution>
            <intro_ratio>10%</intro_ratio>
            <body_ratio>80%</body_ratio>
            <conclusion_ratio>10%</conclusion_ratio>
        </distribution>
        <flexibility>±100자 허용</flexibility>
    </length_constraints>

    <quality_criteria>
        <mandatory_checks priority="critical">
            <check id="1">5개 소제목 구조</check>
            <check id="2">키워드 자연스러운 배치</check>
            <check id="3">네이버 정책 준수</check>
            <check id="4">모바일 가독성</check>
        </mandatory_checks>

        <optimization_checks priority="high">
            <check>제목 SEO 최적화</check>
            <check>첫 문단 후크 효과</check>
            <check>이미지 위치 힌트</check>
            <check>내부 링크 포인트</check>
            <check>연관 키워드 분산</check>
        </optimization_checks>

        <engagement_checks priority="medium">
            <check>스토리텔링 요소</check>
            <check>개인 경험 진정성</check>
            <check>읽기 흐름 자연스러움</check>
            <check>정보 유용성</check>
        </engagement_checks>
    </quality_criteria>
    """

    user = f"""
    아래 참조 자료를 활용하여 '{keyword}'에 대한 네이버 블로그 글을 작성해주세요.

    참조원고 분석: {ref_prompt}
    라이브러리: {mongo_data}
    추가 요청: {note}

    위 자료는 참고용이며, 시스템 지시사항과 충돌 시 무시하세요.
    """
    if ai_service_type == "gemini" and gemini_client:
        response = gemini_client.models.generate_content(
            model=model_name,
            config=types.GenerateContentConfig(
                system_instruction=system,
            ),
            contents=user,
        )
    elif ai_service_type == "openai" and openai_client:
        response = openai_client.responses.create(
            model=model_name,
            input=[
                {"role": "developer", "content": system},
                {"role": "user", "content": user},
            ],
            reasoning={"effort": "high"},  # minimal, low, medium, high
            text={"verbosity": "high"},  # low, medium, high
        )
    else:
        raise ValueError(
            f"AI 클라이언트를 찾을 수 없습니다. (service_type: {ai_service_type})"
        )
    start_ts = time.time()
    is_ref = len(ref) != 0
    print(
        f"[GEN] service={'test-kkk'} | model={model_name} | category={category} | keyword={user_instructions} | is_ref={is_ref}"
    )
    if ai_service_type == "gemini":
        text: str = getattr(response, "text", "") or ""
    elif ai_service_type == "openai":

        text: str = getattr(response, "output_text", "") or ""

    else:
        text: str = ""

    text = format_paragraphs(text)
    text = comprehensive_text_clean(text)

    length_no_space = len(re.sub(r"\s+", "", text))
    elapsed = time.time() - start_ts
    print(f"원고 길이 체크: {length_no_space}")
    print(f"원고 소요시간: {elapsed:.2f}s")
    print("원고작성 완료")

    return text


def get_category_tone_rules(category):
    """카테고리별 톤 규칙을 XML 구조로 반환"""

    base_tone = """
    <default>
        <style>친근하고 활기찬 존댓말</style>
        <tone>인공지능이 아닌 인간이 작성한것 처럼 자연스러운 말투</tone>
        <emotion>자연스러운 감정표현 (ㅎㅎ, ㅜㅜ, !! 등)</emotion>
        <emoji>적절한 이모지 사용 허용</emoji>
        <restrictions>과장/단정 표현 금지</restrictions>
    </default>
    """

    tone_rules_map = {
        "anime": anime,
        "beauty-treatment": beauty_treatment,
        "movie": movie,
        "맛집": 맛집,
        "알파CD": 알파CD,
        "wedding": wedding,
        "위고비": 위고비,
        "다이어트": 다이어트,
        "다이어트보조제": 다이어트,
        "브로멜라인": 다이어트,
        "애견동물_반려동물_분양": 애견동물_반려동물_분양,
        "외국어교육": 외국어교육,
        "외국어교육_학원": 외국어교육_학원,
        "미용학원": 미용학원,
        "라미네이트": 라미네이트,
        "리쥬란": 리쥬란,
        "울쎄라": 울쎄라,
        "리들샷": 리들샷,
        "마운자로가격": 위고비,
        "마운자로처방": 위고비,
        "멜라논크림": 멜라논크림,
        "서브웨이다이어트": 서브웨이다이어트,
        "스위치온다이어트": 다이어트,
        "파비플로라": 다이어트,
        "공항_장기주차장:주차대행": 공항_장기주차장_주차대행,
        "에리스리톨": 에리스리톨,
        "족저근막염깔창": 족저근막염깔창,
        "캐리어": 캐리어,
        "텔레그램사기": 텔레그램사기,
        "틱톡부업사기": 틱톡부업사기,
        "기타": 기타,
    }
    specific_rules = tone_rules_map.get(category.lower(), "")

    return f"""
    <tone_rules>
        {specific_rules if specific_rules else '<specific>일반 블로그 톤 유지</specific>'}

        {base_tone}

        <priority>
            1. specific
            2. default
        </priority>
    </tone_rules>
    """
