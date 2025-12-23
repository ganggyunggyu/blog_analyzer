"""네이버 블로그 글쓰기 자동화 API"""

from __future__ import annotations

import asyncio
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from pathlib import Path

from utils.logger import log

router = APIRouter(prefix="/blog", tags=["blog-write"])

# 디버그 스크린샷 폴더
DEBUG_DIR = Path(__file__).parent.parent.parent / "debug"
DEBUG_DIR.mkdir(exist_ok=True)


class WritePostRequest(BaseModel):
    """글쓰기 요청"""
    cookies: list  # 로그인 쿠키
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    images: Optional[list[str]] = None  # 이미지 경로 목록
    is_public: bool = True  # 전체공개
    schedule_time: Optional[str] = None  # 예약 발행 시간 (ISO format)


class WritePostResponse(BaseModel):
    success: bool
    post_url: Optional[str] = None
    message: str


# 셀렉터 상수
SELECTORS = {
    # 팝업
    "popup_cancel": "button.se-popup-button-cancel",
    "help_close": "button.se-help-panel-close-button",

    # 발행 오버레이
    "publish_btn": "button.publish_btn__m9KHH, button[data-click-area='tpb.publish']",
    "publish_confirm": "button.confirm_btn__WEaBq, button[data-testid='seOnePublishBtn']",

    # 공개 설정
    "open_public": "input#open_public",
    "open_private": "input#open_private",

    # 예약
    "schedule_radio": "input#radio_time2",
    "schedule_hour": "select.hour_option__J_heO",
    "schedule_minute": "select.minute_option__Vb3xB",

    # 날짜 선택기 (datepicker)
    "datepicker_next_month": "button.ui-datepicker-next",
    "datepicker_prev_month": "button.ui-datepicker-prev",
    "datepicker_year": "span.ui-datepicker-year",
    "datepicker_month": "span.ui-datepicker-month",

    # 태그
    "tag_input": "input#tag-input, input.tag_input__rvUB5",

    # 이미지
    "image_btn": "button[data-name='image'], button.se-toolbar-button-image",
}


# ========== 공통 함수들 ==========

async def upload_single_image(frame, page, image_path: str) -> bool:
    """단일 이미지 업로드 (file_chooser 방식)"""
    try:
        # file_chooser 이벤트 대기하면서 이미지 버튼 클릭
        async with page.expect_file_chooser() as fc_info:
            await frame.click(SELECTORS["image_btn"], timeout=5000)

        file_chooser = await fc_info.value
        await file_chooser.set_files(image_path)
        await asyncio.sleep(2)
        log.debug("이미지 업로드", path=Path(image_path).name)
        return True
    except Exception as e:
        log.warning("이미지 업로드 실패", path=Path(image_path).name, error=str(e))
        return False


def is_subheading(line: str) -> bool:
    """부제 패턴 감지 (1., 2., 3., 4., 5. 또는 ①②③④⑤ 등)"""
    import re
    patterns = [
        r"^\d+\.\s",           # 1. 2. 3.
        r"^[①②③④⑤⑥⑦⑧⑨⑩]",  # 원문자
        r"^【\d+】",            # 【1】【2】
        r"^\[\d+\]",           # [1] [2]
        r"^▶\s*\d+",           # ▶1 ▶2
    ]
    for pattern in patterns:
        if re.match(pattern, line.strip()):
            return True
    return False


def match_images_to_subheadings(paragraphs: list[str], images: list[str]) -> dict:
    """부제 위치에 이미지 매핑 (인덱스: 이미지경로)"""
    result = {}
    subheading_indices = []

    for i, para in enumerate(paragraphs):
        if is_subheading(para):
            subheading_indices.append(i)

    # 이미지를 부제 순서대로 매핑
    for idx, img_idx in enumerate(subheading_indices):
        if idx < len(images):
            result[img_idx] = images[idx]

    log.debug("이미지 매핑", subheadings=len(subheading_indices), images=len(images))
    return result


async def close_existing_draft_popup(frame) -> bool:
    """기존 글 팝업 닫기"""
    try:
        await frame.click(SELECTORS["popup_cancel"], timeout=3000)
        await asyncio.sleep(1)
        log.debug("기존 글 팝업 닫음")
        return True
    except:
        return False


async def close_help_panel(frame) -> bool:
    """도움말 패널 닫기"""
    try:
        await frame.click(SELECTORS["help_close"], timeout=3000)
        await asyncio.sleep(0.5)
        return True
    except:
        return False


async def open_publish_overlay(frame) -> bool:
    """발행 오버레이 열기"""
    try:
        await frame.click(SELECTORS["publish_btn"], timeout=10000)
        await asyncio.sleep(2)
        return True
    except Exception as e:
        log.warning("발행 오버레이 오픈 실패", error=str(e))
        return False


async def set_visibility(frame, is_public: bool = True) -> bool:
    """공개 설정"""
    try:
        selector = SELECTORS["open_public"] if is_public else SELECTORS["open_private"]
        await frame.click(selector, timeout=3000)
        return True
    except:
        return False


async def input_tags(frame, page, tags: list[str]) -> bool:
    """태그 입력"""
    if not tags:
        return False
    try:
        tag_input = await frame.wait_for_selector(SELECTORS["tag_input"], timeout=3000)
        for tag in tags[:30]:
            await tag_input.fill(tag)
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.2)
        log.debug("태그 입력", count=len(tags))
        return True
    except:
        return False


async def click_schedule_radio(frame) -> bool:
    """예약 라디오 버튼 클릭"""
    try:
        await frame.click(SELECTORS["schedule_radio"], timeout=3000)
        await asyncio.sleep(1)
        return True
    except Exception as e:
        log.warning("예약 모드 활성화 실패", error=str(e))
        return False


async def set_schedule_date(frame, target_date: datetime) -> bool:
    """예약 날짜 선택 (datepicker)"""
    today = datetime.now().date()
    target = target_date.date()

    if target == today:
        return True

    try:
        current_month = today.month
        current_year = today.year
        target_month = target.month
        target_year = target.year

        month_diff = (target_year - current_year) * 12 + (target_month - current_month)

        for _ in range(month_diff):
            await frame.click(SELECTORS["datepicker_next_month"], timeout=3000)
            await asyncio.sleep(0.5)

        day = target.day
        day_selector = f"td:not(.ui-state-disabled) button.ui-state-default"
        day_buttons = await frame.query_selector_all(day_selector)

        for btn in day_buttons:
            text = await btn.text_content()
            if text and text.strip() == str(day):
                await btn.click()
                await asyncio.sleep(0.5)
                return True

        log.warning("날짜 버튼 찾을 수 없음", day=day)
        return False

    except Exception as e:
        log.warning("날짜 선택 실패", error=str(e))
        return False


async def set_schedule_time(frame, hour: int, minute: int) -> bool:
    """예약 시간 설정"""
    try:
        hour_str = str(hour).zfill(2)
        minute_str = str((minute // 10) * 10).zfill(2)

        await frame.select_option(SELECTORS["schedule_hour"], value=hour_str)
        await asyncio.sleep(0.3)
        await frame.select_option(SELECTORS["schedule_minute"], value=minute_str)
        await asyncio.sleep(0.3)
        return True
    except Exception as e:
        log.warning("예약 시간 설정 실패", error=str(e))
        return False


async def click_final_publish(frame) -> bool:
    """최종 발행 버튼 클릭"""
    try:
        await frame.click(SELECTORS["publish_confirm"], timeout=10000)
        return True
    except Exception as e:
        log.error("최종 발행 실패", error=str(e))
        return False


# ========== 발행 플로우 ==========

async def publish_immediately(frame, page, is_public: bool = True, tags: list[str] = None):
    """즉시 발행 플로우"""
    if not await open_publish_overlay(frame):
        raise RuntimeError("발행 오버레이 오픈 실패")

    await set_visibility(frame, is_public)
    if tags:
        await input_tags(frame, page, tags)

    if not await click_final_publish(frame):
        raise RuntimeError("최종 발행 실패")


async def publish_scheduled(frame, page, schedule_dt: datetime, is_public: bool = True, tags: list[str] = None):
    """예약 발행 플로우"""
    if not await open_publish_overlay(frame):
        raise RuntimeError("발행 오버레이 오픈 실패")

    await set_visibility(frame, is_public)
    if tags:
        await input_tags(frame, page, tags)

    if not await click_schedule_radio(frame):
        raise RuntimeError("예약 모드 활성화 실패")

    # 날짜 선택 (오늘이 아니면)
    if not await set_schedule_date(frame, schedule_dt):
        raise RuntimeError("예약 날짜 설정 실패")

    if not await set_schedule_time(frame, schedule_dt.hour, schedule_dt.minute):
        raise RuntimeError("예약 시간 설정 실패")

    if not await click_final_publish(frame):
        raise RuntimeError("최종 발행 실패")


async def write_blog_post(
    cookies: list,
    title: str,
    content: str,
    category: Optional[str] = None,
    tags: Optional[list[str]] = None,
    images: Optional[list[str]] = None,
    is_public: bool = True,
    schedule_time: Optional[str] = None,
    debug: bool = False,
) -> dict:
    """Playwright로 네이버 블로그 글쓰기"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 실시간 모니터링용
            slow_mo=300,  # 안정적으로 천천히
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # 쿠키 설정
        await context.add_cookies(cookies)

        page = await context.new_page()

        try:
            log.step(1, 5, "글쓰기 페이지 접속")
            await page.goto(
                "https://blog.naver.com/GoBlogWrite.naver",
                wait_until="domcontentloaded",
                timeout=30000,
            )

            await asyncio.sleep(3)

            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "write_step1_page.png"))

            frame = page.frame(name="mainFrame")
            if not frame:
                raise RuntimeError("mainFrame을 찾을 수 없습니다")

            await asyncio.sleep(2)

            log.step(2, 5, "팝업 처리")
            await close_existing_draft_popup(frame)
            await close_help_panel(frame)

            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "write_step2_popup.png"))

            try:
                editor = await frame.wait_for_selector(
                    'div.se-component-content, div[contenteditable="true"], p.se-text-paragraph',
                    timeout=5000
                )
                if editor:
                    await editor.click()
                    await asyncio.sleep(0.5)
            except:
                pass

            log.step(3, 5, f"콘텐츠 입력 ({len(content)}자)")
            full_text = f"{title}\n{content}"
            paragraphs = full_text.split('\n')

            image_map = {}
            if images:
                image_map = match_images_to_subheadings(paragraphs, images)

            for i, para in enumerate(paragraphs):
                if para.strip():
                    await page.keyboard.type(para.strip(), delay=10)

                if i < len(paragraphs) - 1:
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(0.1)

                # 부제 다음에 이미지 삽입
                if i in image_map:
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(0.3)
                    await upload_single_image(frame, page, image_map[i])
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(0.3)

            await asyncio.sleep(1)
            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "write_step3_content.png"))

            log.step(4, 5, "발행 설정")
            if schedule_time:
                if isinstance(schedule_time, str):
                    schedule_dt = datetime.fromisoformat(schedule_time)
                else:
                    schedule_dt = schedule_time
                await publish_scheduled(frame, page, schedule_dt, is_public, tags)
            else:
                await publish_immediately(frame, page, is_public, tags)

            await asyncio.sleep(3)
            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "write_step4_done.png"))

            log.step(5, 5, "발행 완료")
            current_url = page.url
            log.success("글 발행 완료", url=current_url[:50])

            await browser.close()

            return {
                "success": True,
                "post_url": current_url,
                "message": "글 발행 완료",
            }

        except PlaywrightTimeout as e:
            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "write_error_timeout.png"))
            await browser.close()
            return {
                "success": False,
                "post_url": None,
                "message": f"타임아웃: {str(e)}",
            }

        except Exception as e:
            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "write_error_unknown.png"))
            await browser.close()
            return {
                "success": False,
                "post_url": None,
                "message": f"에러: {str(e)}",
            }


@router.post("/write")
async def write_post(request: WritePostRequest):
    """블로그 글쓰기 API"""

    log.header("블로그 글쓰기", "📝")
    log.kv("제목", request.title[:40])

    result = await write_blog_post(
        cookies=request.cookies,
        title=request.title,
        content=request.content,
        category=request.category,
        tags=request.tags,
        is_public=request.is_public,
        schedule_time=request.schedule_time,
        debug=True,  # 디버그 모드
    )

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "WRITE_FAILED",
                "message": result["message"],
            },
        )

    return JSONResponse(content=result)


@router.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok", "service": "blog-write"}
