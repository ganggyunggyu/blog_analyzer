"""네이버 블로그 글쓰기 자동화 서비스"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import Frame
from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

from utils.logger import log


DEBUG_DIR = Path(__file__).parent.parent / "debug"
DEBUG_DIR.mkdir(exist_ok=True)

SELECTORS = {
    "popup_cancel": "button.se-popup-button-cancel",
    "help_close": "button.se-help-panel-close-button",
    "publish_btn": "button.publish_btn__m9KHH, button[data-click-area='tpb.publish']",
    "publish_confirm": "button.confirm_btn__WEaBq, button[data-testid='seOnePublishBtn']",
    "open_public": "input#open_public",
    "open_private": "input#open_private",
    "schedule_radio": "label[for='radio_time2'], label.radio_label__mB6ia",
    "schedule_hour": "select.hour_option__J_heO",
    "schedule_minute": "select.minute_option__Vb3xB",
    "date_input": "input.input_date__QmA0s",
    "datepicker_next_month": "button.ui-datepicker-next",
    "datepicker_prev_month": "button.ui-datepicker-prev",
    "datepicker_year": "span.ui-datepicker-year",
    "datepicker_month": "span.ui-datepicker-month",
    "tag_input": "input#tag-input, input.tag_input__rvUB5",
    "image_btn": "button[data-name='image'], button.se-toolbar-button-image",
}

EDITOR_SELECTOR = (
    'div.se-component-content, div[contenteditable="true"], p.se-text-paragraph'
)


async def _capture_debug_screenshot(page: Page, filename: str, debug: bool) -> None:
    if not debug:
        return

    try:
        await page.screenshot(path=str(DEBUG_DIR / filename))
    except Exception as error:
        log.warning("디버그 스크린샷 실패", file=filename, error=str(error))


async def upload_single_image(frame: Frame, page: Page, image_path: str) -> bool:
    """단일 이미지 업로드 (file_chooser 방식)"""
    try:
        async with page.expect_file_chooser() as file_chooser_info:
            await frame.click(SELECTORS["image_btn"], timeout=5000)

        file_chooser = await file_chooser_info.value
        await file_chooser.set_files(image_path)
        await asyncio.sleep(2)
        log.debug("이미지 업로드", path=Path(image_path).name)
        return True
    except Exception as error:
        log.warning("이미지 업로드 실패", path=Path(image_path).name, error=str(error))
        return False


def is_subheading(line: str) -> bool:
    """부제 패턴 감지 (1., 2., 3., 4., 5. 또는 ①②③④⑤ 등)"""
    patterns = [
        r"^\d+\.\s",
        r"^[①②③④⑤⑥⑦⑧⑨⑩]",
        r"^【\d+】",
        r"^\[\d+\]",
        r"^▶\s*\d+",
    ]
    stripped_line = line.strip()
    for pattern in patterns:
        if re.match(pattern, stripped_line):
            return True
    return False


def match_images_to_subheadings(paragraphs: list[str], images: list[str]) -> dict[int, str]:
    """부제 위치에 이미지 매핑 (인덱스: 이미지경로)"""
    image_map: dict[int, str] = {}
    subheading_indices: list[int] = []

    for index, paragraph in enumerate(paragraphs):
        if is_subheading(paragraph):
            subheading_indices.append(index)

    for index, subheading_index in enumerate(subheading_indices):
        if index < len(images):
            image_map[subheading_index] = images[index]

    log.debug("이미지 매핑", subheadings=len(subheading_indices), images=len(images))
    return image_map


async def close_existing_draft_popup(frame: Frame) -> bool:
    """기존 글 팝업 닫기"""
    try:
        await frame.click(SELECTORS["popup_cancel"], timeout=3000)
        await asyncio.sleep(1)
        log.debug("기존 글 팝업 닫음")
        return True
    except Exception:
        return False


async def close_help_panel(frame: Frame) -> bool:
    """도움말 패널 닫기"""
    try:
        await frame.click(SELECTORS["help_close"], timeout=3000)
        await asyncio.sleep(0.5)
        return True
    except Exception:
        return False


async def open_publish_overlay(frame: Frame) -> bool:
    """발행 오버레이 열기"""
    try:
        await frame.click(SELECTORS["publish_btn"], timeout=10000)
        await asyncio.sleep(2)
        return True
    except Exception as error:
        log.warning("발행 오버레이 오픈 실패", error=str(error))
        return False


async def set_visibility(frame: Frame, is_public: bool = True) -> bool:
    """공개 설정"""
    try:
        selector = SELECTORS["open_public"] if is_public else SELECTORS["open_private"]
        await frame.click(selector, timeout=3000)
        return True
    except Exception:
        return False


async def input_tags(frame: Frame, page: Page, tags: Optional[list[str]]) -> bool:
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
    except Exception:
        return False


async def click_schedule_radio(frame: Frame) -> bool:
    """예약 라디오 버튼 클릭"""
    try:
        label = frame.locator('label[for="radio_time2"]')
        if await label.count() > 0:
            await label.click(timeout=5000)
            log.debug("예약 레이블 클릭 완료")
            await asyncio.sleep(1)
        else:
            label = frame.get_by_text("예약", exact=True)
            await label.click(timeout=5000)
            log.debug("예약 텍스트 클릭 완료")
            await asyncio.sleep(1)

        time_setting_selector = "div.time_setting__v6YRU, div[class*='time_setting']"
        try:
            await frame.wait_for_selector(time_setting_selector, timeout=5000)
            log.debug("예약 시간 설정 영역 활성화됨")
        except Exception:
            log.debug("time_setting 안 보임 - 재시도")
            await label.click(force=True)
            await asyncio.sleep(1)

        try:
            await frame.wait_for_selector(SELECTORS["schedule_hour"], timeout=5000)
            log.debug("예약 시간 선택기 활성화됨")
            return True
        except Exception:
            log.warning("시간 선택기가 나타나지 않음")
            return False

    except Exception as error:
        log.warning("예약 모드 활성화 실패", error=str(error))
        return False


async def set_schedule_date(frame: Frame, target_date: datetime) -> bool:
    """예약 날짜 선택 (datepicker)"""
    today = datetime.now().date()
    target = target_date.date()

    if target == today:
        return True

    try:
        date_input = frame.locator(SELECTORS["date_input"])
        await date_input.click(timeout=3000)
        await asyncio.sleep(0.5)

        datepicker = frame.locator(".ui-datepicker-header")
        await datepicker.wait_for(state="visible", timeout=3000)
        log.debug("캘린더 열림")

        current_month = today.month
        current_year = today.year
        target_month = target.month
        target_year = target.year
        month_diff = (target_year - current_year) * 12 + (target_month - current_month)

        for _ in range(month_diff):
            await frame.click(SELECTORS["datepicker_next_month"], timeout=3000)
            await asyncio.sleep(0.5)

        day_selector = "td:not(.ui-state-disabled) button.ui-state-default"
        day_buttons = await frame.query_selector_all(day_selector)

        for button in day_buttons:
            text = await button.text_content()
            if text and text.strip() == str(target.day):
                await button.click()
                await asyncio.sleep(0.5)
                log.debug("날짜 선택 완료", day=target.day)
                return True

        log.warning("날짜 버튼 찾을 수 없음", day=target.day)
        return False

    except Exception as error:
        log.warning("날짜 선택 실패", error=str(error))
        return False


async def set_schedule_time(frame: Frame, hour: int, minute: int) -> bool:
    """예약 시간 설정"""
    try:
        hour_str = str(hour).zfill(2)
        minute_str = str((minute // 10) * 10).zfill(2)

        log.debug("예약 시간 설정 시도", hour=hour_str, minute=minute_str)

        hour_select = frame.locator(SELECTORS["schedule_hour"])
        await hour_select.wait_for(timeout=5000)
        await hour_select.select_option(value=hour_str)
        await asyncio.sleep(0.5)

        minute_select = frame.locator(SELECTORS["schedule_minute"])
        await minute_select.wait_for(timeout=5000)
        await minute_select.select_option(value=minute_str)
        await asyncio.sleep(0.5)

        log.debug("예약 시간 설정 완료", time=f"{hour_str}:{minute_str}")
        return True
    except Exception as error:
        log.warning("예약 시간 설정 실패", error=str(error))
        return False


async def click_final_publish(frame: Frame) -> bool:
    """최종 발행 버튼 클릭"""
    try:
        await frame.click(SELECTORS["publish_confirm"], timeout=10000)
        return True
    except Exception as error:
        log.error("최종 발행 실패", error=str(error))
        return False


async def publish_immediately(
    frame: Frame,
    page: Page,
    is_public: bool = True,
    tags: Optional[list[str]] = None,
) -> None:
    """즉시 발행 플로우"""
    if not await open_publish_overlay(frame):
        raise RuntimeError("발행 오버레이 오픈 실패")

    await set_visibility(frame, is_public)
    if tags:
        await input_tags(frame, page, tags)

    if not await click_final_publish(frame):
        raise RuntimeError("최종 발행 실패")


async def publish_scheduled(
    frame: Frame,
    page: Page,
    schedule_dt: datetime,
    is_public: bool = True,
    tags: Optional[list[str]] = None,
) -> None:
    """예약 발행 플로우"""
    if not await open_publish_overlay(frame):
        raise RuntimeError("발행 오버레이 오픈 실패")

    await set_visibility(frame, is_public)
    if tags:
        await input_tags(frame, page, tags)

    if not await click_schedule_radio(frame):
        raise RuntimeError("예약 모드 활성화 실패")

    if not await set_schedule_date(frame, schedule_dt):
        raise RuntimeError("예약 날짜 설정 실패")

    if not await set_schedule_time(frame, schedule_dt.hour, schedule_dt.minute):
        raise RuntimeError("예약 시간 설정 실패")

    if not await click_final_publish(frame):
        raise RuntimeError("최종 발행 실패")


async def _focus_editor(frame: Frame) -> None:
    try:
        editor = await frame.wait_for_selector(EDITOR_SELECTOR, timeout=5000)
        if editor:
            await editor.click()
            await asyncio.sleep(0.5)
    except Exception:
        return


async def _write_editor_content(
    page: Page,
    frame: Frame,
    title: str,
    content: str,
    images: Optional[list[str]],
) -> None:
    full_text = f"{title}\n{content}"
    paragraphs = full_text.split("\n")
    image_map = match_images_to_subheadings(paragraphs, images) if images else {}

    previous_was_list = False
    for index, paragraph in enumerate(paragraphs):
        text = paragraph.strip()
        if text:
            is_list = text.startswith("- ")
            if is_list and previous_was_list:
                text = text[2:]
            await page.keyboard.type(text, delay=10)
            previous_was_list = is_list
        else:
            previous_was_list = False

        if index < len(paragraphs) - 1:
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.1)

        if index in image_map:
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.3)
            await upload_single_image(frame, page, image_map[index])
            await page.keyboard.press("Enter")
            await asyncio.sleep(0.3)


def _parse_schedule_time(schedule_time: Optional[str]) -> Optional[datetime]:
    if not schedule_time:
        return None
    return datetime.fromisoformat(schedule_time)


def _build_success_result(post_url: str) -> dict[str, Optional[str] | bool]:
    return {
        "success": True,
        "post_url": post_url,
        "message": "글 발행 완료",
    }


def _build_error_result(message: str) -> dict[str, Optional[str] | bool]:
    return {
        "success": False,
        "post_url": None,
        "message": message,
    }


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
) -> dict[str, Optional[str] | bool]:
    """Playwright로 네이버 블로그 글쓰기"""
    del category

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False, slow_mo=300)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
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
            await _capture_debug_screenshot(page, "write_step1_page.png", debug)

            frame = page.frame(name="mainFrame")
            if not frame:
                raise RuntimeError("mainFrame을 찾을 수 없습니다")

            await asyncio.sleep(2)

            log.step(2, 5, "팝업 처리")
            await close_existing_draft_popup(frame)
            await close_help_panel(frame)
            await _capture_debug_screenshot(page, "write_step2_popup.png", debug)

            await _focus_editor(frame)

            log.step(3, 5, f"콘텐츠 입력 ({len(content)}자)")
            await _write_editor_content(page, frame, title, content, images)
            await asyncio.sleep(1)
            await _capture_debug_screenshot(page, "write_step3_content.png", debug)

            log.step(4, 5, "발행 설정")
            schedule_dt = _parse_schedule_time(schedule_time)
            if schedule_dt:
                await publish_scheduled(frame, page, schedule_dt, is_public, tags)
            else:
                await publish_immediately(frame, page, is_public, tags)

            await asyncio.sleep(3)
            await _capture_debug_screenshot(page, "write_step4_done.png", debug)

            log.step(5, 5, "발행 완료")
            current_url = page.url
            log.success("글 발행 완료", url=current_url[:50])
            return _build_success_result(current_url)

        except PlaywrightTimeout as error:
            await _capture_debug_screenshot(page, "write_error_timeout.png", debug)
            return _build_error_result(f"타임아웃: {str(error)}")
        except Exception as error:
            await _capture_debug_screenshot(page, "write_error_unknown.png", debug)
            return _build_error_result(f"에러: {str(error)}")
        finally:
            await browser.close()


__all__ = [
    "write_blog_post",
]
