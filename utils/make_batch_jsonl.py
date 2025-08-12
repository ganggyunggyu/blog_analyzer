import json, uuid

def make_batch_jsonl(rows, model="gpt-4.1-2025-04-14"):
    """
    rows: list[dict] — 각 dict는 {unique_words, sentences, expressions, parameters, user_instructions, ref}
    return: jsonl string
    """
    lines = []
    for i, r in enumerate(rows):
        prompt = f"""
[고유 단어 리스트]
{", ".join(r.get("unique_words") or []) or "없음"}

[표현 라이브러리]
{json.dumps(r.get("expressions") or {}, ensure_ascii=False, indent=2) or "없음"}

[AI 개체 인식 및 그룹화 결과]
{json.dumps(r.get("parameters") or {}, ensure_ascii=False, indent=2) or "없음"}

[사용자 지시사항]
{r.get("user_instructions")}

[참고 문서]
{r.get("ref") or ""}

[요청]
- 공백 제거 기준으로 1700~2000 글자 사이가 되도록 조절해줘.
- 중간에 끊기지 말고 반드시 완결된 원고로 마무리해.
"""
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a professional blog post writer."},
                {"role": "user", "content": prompt}
            ],
            "max_completion_tokens": 2200,
        }
        lines.append({
            "custom_id": f"draft-{i}-{uuid.uuid4().hex[:8]}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": body
        })
    return "\n".join(json.dumps(x, ensure_ascii=False) for x in lines)