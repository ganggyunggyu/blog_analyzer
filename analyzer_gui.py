"""
Analyzer GUI - Streamlit 기반 텍스트 분석 도구

실행 방법:
    streamlit run analyzer_gui.py

기존 analyzer 모듈을 import하여 사용 (코드 훼손 없음)
"""

import streamlit as st
import json
from typing import Dict, List

# analyzer 모듈 import
from analyzer.sentence import split_sentences
from analyzer.morpheme import analyze_morphemes
from analyzer.subtitle import gen_subtitles
from analyzer.expression import gen_expressions
from analyzer.template import template_gen
from _constants.categories import CATEGORIES


def main():
    st.set_page_config(
        page_title="Blog Analyzer GUI",
        page_icon="📊",
        layout="wide",
    )

    st.title("📊 Blog Analyzer GUI")
    st.markdown("텍스트 분석 도구 - 기존 analyzer 모듈 활용")

    # 사이드바 - 공통 설정
    with st.sidebar:
        st.header("⚙️ 공통 설정")

        category = st.selectbox(
            "카테고리 선택",
            options=[""] + CATEGORIES,
            index=0,
            help="MongoDB 저장 시 사용할 카테고리",
        )

        file_name = st.text_input(
            "파일명 (선택)",
            placeholder="example.txt",
            help="분석 결과 저장 시 파일명으로 사용",
        )

        save_to_db = st.checkbox(
            "MongoDB에 저장",
            value=False,
            help="체크하면 분석 결과를 MongoDB에 저장",
        )

        st.divider()
        st.markdown("### 📌 사용 팁")
        st.markdown("""
        1. 텍스트 입력 후 분석 버튼 클릭
        2. AI 분석은 시간이 걸릴 수 있음
        3. MongoDB 저장은 카테고리 필수
        """)

    # 메인 영역 - 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 문장 분리",
        "🔤 형태소 분석",
        "📑 소제목 추출",
        "💬 표현 추출",
        "📄 템플릿 생성",
    ])

    # 탭 1: 문장 분리
    with tab1:
        st.header("📝 문장 분리")
        st.markdown("텍스트를 문장 단위로 분리합니다. (AI 미사용)")

        text_sentence = st.text_area(
            "분석할 텍스트",
            height=200,
            key="text_sentence",
            placeholder="여기에 텍스트를 입력하세요...",
        )

        if st.button("문장 분리 실행", key="btn_sentence"):
            if text_sentence.strip():
                with st.spinner("문장 분리 중..."):
                    cat = category if save_to_db else ""
                    fname = file_name if save_to_db else ""
                    sentences = split_sentences(text_sentence, cat, fname)

                st.success(f"✅ 분리된 문장: {len(sentences)}개")

                for i, sentence in enumerate(sentences, 1):
                    st.markdown(f"**{i}.** {sentence}")
            else:
                st.warning("텍스트를 입력해주세요.")

    # 탭 2: 형태소 분석
    with tab2:
        st.header("🔤 형태소 분석")
        st.markdown("텍스트에서 2글자 이상 한글 단어를 추출합니다. (AI 미사용)")

        text_morpheme = st.text_area(
            "분석할 텍스트",
            height=200,
            key="text_morpheme",
            placeholder="여기에 텍스트를 입력하세요...",
        )

        if st.button("형태소 분석 실행", key="btn_morpheme"):
            if text_morpheme.strip():
                with st.spinner("형태소 분석 중..."):
                    cat = category if save_to_db else ""
                    fname = file_name if save_to_db else ""
                    morphemes = analyze_morphemes(text_morpheme, cat, fname)

                st.success(f"✅ 추출된 형태소: {len(morphemes)}개")

                # 태그 형태로 표시
                morpheme_html = " ".join(
                    [f'<span style="background-color:#e8f4ea;padding:4px 8px;margin:2px;border-radius:4px;display:inline-block;">{m}</span>'
                     for m in sorted(morphemes)]
                )
                st.markdown(morpheme_html, unsafe_allow_html=True)
            else:
                st.warning("텍스트를 입력해주세요.")

    # 탭 3: 소제목 추출
    with tab3:
        st.header("📑 소제목 추출")
        st.markdown("AI를 사용하여 블로그 원고에서 소제목을 추출합니다.")

        col1, col2 = st.columns([3, 1])
        with col2:
            max_subtitles = st.number_input(
                "최대 개수",
                min_value=1,
                max_value=10,
                value=5,
            )

        text_subtitle = st.text_area(
            "분석할 텍스트",
            height=200,
            key="text_subtitle",
            placeholder="여기에 블로그 원고를 입력하세요...",
        )

        if st.button("소제목 추출 실행", key="btn_subtitle", type="primary"):
            if text_subtitle.strip():
                with st.spinner("🤖 AI가 소제목을 추출하고 있습니다..."):
                    cat = category if save_to_db else ""
                    fname = file_name if save_to_db else ""
                    subtitles = gen_subtitles(
                        text_subtitle, cat, fname, max_items=max_subtitles
                    )

                st.success(f"✅ 추출된 소제목: {len(subtitles)}개")

                for i, subtitle in enumerate(subtitles, 1):
                    st.markdown(f"### {i}. {subtitle}")
            else:
                st.warning("텍스트를 입력해주세요.")

    # 탭 4: 표현 추출
    with tab4:
        st.header("💬 표현 추출")
        st.markdown("AI를 사용하여 마케팅/콘텐츠 제작에 유용한 표현을 추출합니다.")

        text_expression = st.text_area(
            "분석할 텍스트",
            height=200,
            key="text_expression",
            placeholder="여기에 블로그 원고를 입력하세요...",
        )

        if st.button("표현 추출 실행", key="btn_expression", type="primary"):
            if text_expression.strip():
                with st.spinner("🤖 AI가 표현을 추출하고 있습니다..."):
                    cat = category if save_to_db else ""
                    fname = file_name if save_to_db else ""
                    expressions = gen_expressions(text_expression, cat, fname)

                if expressions:
                    st.success(f"✅ 추출된 표현 카테고리: {len(expressions)}개")

                    for cat_name, exprs in expressions.items():
                        with st.expander(f"📁 {cat_name} ({len(exprs)}개)", expanded=True):
                            for expr in exprs:
                                st.markdown(f"- {expr}")
                else:
                    st.info("추출된 표현이 없습니다.")
            else:
                st.warning("텍스트를 입력해주세요.")

    # 탭 5: 템플릿 생성
    with tab5:
        st.header("📄 템플릿 생성")
        st.markdown("AI를 사용하여 텍스트를 템플릿화합니다. (변수 치환)")

        if not category:
            st.warning("⚠️ 템플릿 생성은 카테고리 선택이 필수입니다.")
        else:
            text_template = st.text_area(
                "원본 텍스트",
                height=200,
                key="text_template",
                placeholder="여기에 원본 텍스트를 입력하세요...",
            )

            user_instructions = st.text_area(
                "추가 지시사항 (선택)",
                height=100,
                key="user_instructions",
                placeholder="예: 상호명과 가격을 변수로 치환해주세요",
            )

            if st.button("템플릿 생성 실행", key="btn_template", type="primary"):
                if text_template.strip():
                    with st.spinner("🤖 AI가 템플릿을 생성하고 있습니다... (시간이 걸릴 수 있습니다)"):
                        fname = file_name if file_name else ""
                        templated = template_gen(
                            user_instructions=user_instructions,
                            docs=text_template,
                            category=category,
                            file_name=fname,
                        )

                    st.success("✅ 템플릿 생성 완료!")

                    st.subheader("생성된 템플릿")
                    st.code(templated, language="text")

                    # 복사 버튼
                    st.download_button(
                        label="📋 템플릿 다운로드",
                        data=templated,
                        file_name=f"template_{file_name or 'output'}.txt",
                        mime="text/plain",
                    )
                else:
                    st.warning("텍스트를 입력해주세요.")


if __name__ == "__main__":
    main()
