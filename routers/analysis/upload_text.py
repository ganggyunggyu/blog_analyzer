from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])

PREVIEW_LEN = 300


def _decode_text(b: bytes) -> str:
    """
    txt 파일 인코딩 추정
    - 우선 utf-8-sig → utf-8 → cp949 순서로 시도
    """
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            return b.decode(enc)
        except Exception:
            continue

    raise UnicodeDecodeError("unknown", b, 0, 1, "unsupported encoding")


@router.post("/upload-text")
async def upload_text(files: list[UploadFile] = File(...)):
    """
    다중 txt 파일 업로드 → 각 파일 텍스트 읽어 배열로 반환
    단일 파일만 올려도 동일한 인터페이스로 처리
    """
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="업로드된 파일이 없습니다")

    results = []
    for f in files:
        try:

            name = f.filename or "unknown.txt"
            if (
                not name.lower().endswith(".txt")
                and (f.content_type or "").lower() != "text/plain"
            ):
                raise HTTPException(
                    status_code=400, detail=f"{name}: txt 파일만 업로드 가능합니다"
                )

            raw = await f.read()
            text = _decode_text(raw)

            results.append(
                {
                    "ok": True,
                    "filename": name,
                    "length": len(text),
                    "preview": text[:PREVIEW_LEN],
                    "full_text": text,
                }
            )
        except HTTPException as he:

            results.append(
                {
                    "ok": False,
                    "filename": f.filename or "unknown",
                    "error": he.detail,
                }
            )
        except Exception as e:
            results.append(
                {
                    "ok": False,
                    "filename": f.filename or "unknown",
                    "error": f"파일 처리 실패: {e}",
                }
            )

        res = JSONResponse(
            content={
                "ok": True,
                "count": len(results),
                "results": results,
            }
        )

        print(res)

    return res
