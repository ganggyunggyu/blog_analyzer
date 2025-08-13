from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
import re, hashlib
import kss

router = APIRouter(prefix="/manuscript", tags=["manuscript"])


MAX_TEXT_LEN = 100000000000000000000
MAX_KEYWORDS = 32

class ManuscriptIn(BaseModel):
    text: str = Field(..., min_length=1, description="원고 전체 텍스트")
    keywords: List[str] = Field(default_factory=list, description="타깃 키워드 리스트")

class ManuscriptAck(BaseModel):
    docId: str
    charCount: int
    sentenceCount: int
    keywordCount: int
    keywords: List[str]

def _split_sentences(t: str) -> list[str]:
    return [s.strip() for s in kss.split_sentences(t)]

@router.post("/ingest", response_model=ManuscriptAck, summary="원고와 키워드 받기")
async def ingest_manuscript(payload: ManuscriptIn):
    text = payload.text.strip()
    if not text:
        raise HTTPException(400, "text 비어있음")
    if len(text) > MAX_TEXT_LEN:
        raise HTTPException(413, f"text 길이 초과({MAX_TEXT_LEN}자 제한)")

    kw_list: List[str] = []
    for k in payload.keywords[:MAX_KEYWORDS]:
        k = k.strip()
        if not k:
            continue
        if len(k) > 60:
            raise HTTPException(400, f"키워드 너무 김: {k[:20]}...")
        if k not in kw_list:
            kw_list.append(k)

    doc_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return ManuscriptAck(
        docId=doc_id,
        charCount=len(text),
        sentenceCount=len(_split_sentences(text)),
        keywordCount=len(kw_list),
        keywords=kw_list,
    )