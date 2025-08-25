from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/upload-text")
async def upload_text(file: UploadFile = File(...)):
    """
    txt 파일 업로드 -> 텍스트 읽기 (AI 호출 없이 반환)
    """
    try:
        if file.filename == None:
            raise HTTPException(status_code=400, detail="파일이 없습니다.")
        if not file.filename.endswith(".txt"):
            raise HTTPException(status_code=400, detail="txt 파일만 업로드 가능합니다.")

        content = await file.read()
        text = content.decode("utf-8")

        result = JSONResponse(
            content={
                "ok": True,
                "filename": file.filename,
                "length": len(text),
                "preview": text[:300],  # 앞부분만 미리보기
                "full_text": text,
            }
        )
        print(result)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 처리 실패: {str(e)}")
