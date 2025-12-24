"""원고 업로드 API (ZIP)"""

import zipfile
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from utils.logger import log

from .common import PENDING_DIR, get_manuscript_list

router = APIRouter()


@router.post("/upload")
async def upload_manuscripts(file: UploadFile = File(...)):
    """ZIP 파일로 원고 업로드

    ZIP 구조:
    ```
    upload.zip
    ├── 탈모/
    │   ├── 탈모.txt (첫 줄=제목, 나머지=본문)
    │   └── 1.png, 2.png ... (이미지, 선택)
    └── 위고비/
        ├── 위고비.txt
        └── images/
            └── 1.png
    ```
    """
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="ZIP 파일만 업로드 가능합니다.")

    log.header("ZIP 업로드", "📦")
    log.kv("파일명", file.filename)

    # 임시 파일로 저장
    with NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    uploaded = []
    skipped = []

    try:
        with zipfile.ZipFile(tmp_path, "r") as zf:
            # ZIP 내 최상위 폴더들 추출
            top_folders = set()
            for name in zf.namelist():
                parts = name.split("/")
                if len(parts) > 1 and parts[0]:
                    top_folders.add(parts[0])

            log.kv("폴더 수", len(top_folders))

            for folder_name in top_folders:
                # __MACOSX 등 시스템 폴더 무시
                if folder_name.startswith("__") or folder_name.startswith("."):
                    continue

                dst_dir = PENDING_DIR / folder_name

                # 이미 존재하면 스킵
                if dst_dir.exists():
                    skipped.append(folder_name)
                    log.warning(f"이미 존재: {folder_name}")
                    continue

                dst_dir.mkdir(parents=True, exist_ok=True)

                # 해당 폴더 내 파일들 추출
                for name in zf.namelist():
                    if not name.startswith(folder_name + "/"):
                        continue

                    # 상대 경로 계산
                    rel_path = name[len(folder_name) + 1:]
                    if not rel_path or rel_path.endswith("/"):
                        continue

                    # 파일 추출
                    target_path = dst_dir / rel_path
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    with zf.open(name) as src:
                        with open(target_path, "wb") as dst:
                            dst.write(src.read())

                uploaded.append(folder_name)
                log.success(f"업로드 완료: {folder_name}")

    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="잘못된 ZIP 파일입니다.")
    finally:
        # 임시 파일 삭제
        tmp_path.unlink(missing_ok=True)

    log.divider()
    log.success("업로드 완료", 성공=len(uploaded), 스킵=len(skipped))

    return JSONResponse(content={
        "success": True,
        "uploaded": uploaded,
        "skipped": skipped,
        "message": f"{len(uploaded)}개 폴더가 pending에 추가되었습니다.",
    })


@router.get("/pending")
async def get_pending_list():
    """pending 원고 목록"""
    manuscripts = get_manuscript_list("pending")
    return JSONResponse(content={
        "count": len(manuscripts),
        "manuscripts": [m.model_dump() for m in manuscripts],
    })


@router.delete("/pending/{manuscript_id}")
async def delete_pending(manuscript_id: str):
    """pending 원고 삭제"""
    manuscript_dir = PENDING_DIR / manuscript_id
    if not manuscript_dir.exists():
        raise HTTPException(status_code=404, detail="원고를 찾을 수 없습니다.")

    shutil.rmtree(manuscript_dir)

    return JSONResponse(content={
        "success": True,
        "message": f"원고 {manuscript_id}가 삭제되었습니다.",
    })


@router.delete("/pending")
async def clear_pending():
    """pending 전체 삭제"""
    count = 0
    for folder in PENDING_DIR.iterdir():
        if folder.is_dir():
            shutil.rmtree(folder)
            count += 1

    return JSONResponse(content={
        "success": True,
        "deleted": count,
        "message": f"{count}개 원고가 삭제되었습니다.",
    })
