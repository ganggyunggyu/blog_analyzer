"""네이버 로그인 프록시 API"""

from __future__ import annotations

import uuid
import asyncio
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from pathlib import Path

from utils.logger import log

router = APIRouter(prefix="/auth/naver", tags=["naver-auth"])

# 디버그 스크린샷 폴더
DEBUG_DIR = Path(__file__).parent.parent.parent / "debug"
DEBUG_DIR.mkdir(exist_ok=True)


class LoginRequest(BaseModel):
    id: str
    password: str


class LogoutRequest(BaseModel):
    sessionId: str


class SessionData:
    def __init__(self, cookies: list, created_at: datetime):
        self.cookies = cookies
        self.created_at = created_at
        self.last_used = created_at


# 인메모리 세션 저장소 (프로덕션에서는 Redis 권장)
sessions: dict[str, SessionData] = {}

# Rate limiting
login_attempts: dict[str, list[datetime]] = {}
RATE_LIMIT = 5  # 분당 최대 시도 횟수
RATE_WINDOW = 60  # 초


def check_rate_limit(client_ip: str) -> bool:
    """Rate limiting 체크"""
    now = datetime.now()
    window_start = now - timedelta(seconds=RATE_WINDOW)

    if client_ip not in login_attempts:
        login_attempts[client_ip] = []

    # 윈도우 외 시도 제거
    login_attempts[client_ip] = [
        t for t in login_attempts[client_ip] if t > window_start
    ]

    if len(login_attempts[client_ip]) >= RATE_LIMIT:
        return False

    login_attempts[client_ip].append(now)
    return True


async def naver_login_with_playwright(
    account_id: str, password: str, debug: bool = False
) -> dict:
    """Playwright로 네이버 로그인 수행"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # headless=True면 봇으로 감지됨
            slow_mo=100 if debug else 0,
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            log.step(1, 6, "로그인 페이지 접속")
            await page.goto(
                "https://nid.naver.com/nidlogin.login",
                wait_until="domcontentloaded",
                timeout=30000,
            )
            await asyncio.sleep(1)

            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "login_step1_page.png"))

            # 캡챠 감지
            captcha = await page.query_selector("#captcha")
            if captcha:
                log.warning("캡챠 감지됨")
                await browser.close()
                return {
                    "success": False,
                    "error": "CAPTCHA_REQUIRED",
                    "message": "캡챠가 감지되었습니다. 잠시 후 다시 시도해주세요.",
                }

            log.step(2, 6, "ID 입력")
            await page.evaluate(
                f"""
                document.querySelector('#id').value = '{account_id}';
                document.querySelector('#id').dispatchEvent(new Event('input', {{ bubbles: true }}));
            """
            )

            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "login_step2_id.png"))

            log.step(3, 6, "PW 입력")
            await page.evaluate(
                f"""
                document.querySelector('#pw').value = '{password}';
                document.querySelector('#pw').dispatchEvent(new Event('input', {{ bubbles: true }}));
            """
            )

            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "login_step3_pw.png"))

            log.step(4, 6, "로그인 버튼 클릭")
            await page.click(".btn_login, #log\\.login, button[type='submit']")

            log.step(5, 6, "페이지 이동 대기")
            try:
                await page.wait_for_url(
                    lambda url: "nid.naver.com/nidlogin" not in url,
                    timeout=10000
                )
            except PlaywrightTimeout:
                pass

            await asyncio.sleep(2)

            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "login_step4_result.png"))

            # 로그인 실패 체크
            error_msg = await page.query_selector(".error_message, #err_common")
            if error_msg:
                error_text = await error_msg.text_content()
                log.warning("로그인 실패", error=error_text)
                await browser.close()
                return {
                    "success": False,
                    "error": "LOGIN_FAILED",
                    "message": f"로그인 실패: {error_text}",
                }

            # 2차 인증 체크
            two_factor = await page.query_selector(
                "#new_device_confirm, .sp_ti_login"
            )
            if two_factor:
                log.warning("2차 인증 필요")
                await browser.close()
                return {
                    "success": False,
                    "error": "TWO_FACTOR_REQUIRED",
                    "message": "2차 인증이 필요합니다.",
                }

            log.step(6, 6, "쿠키 추출")
            cookies = await context.cookies()

            cookie_names = [name for c in cookies if (name := c.get("name"))]
            required_cookies = ["NID_AUT", "NID_SES"]

            if not all(name in cookie_names for name in required_cookies):
                current_url = page.url
                if "nid.naver.com" in current_url:
                    log.warning("로그인 미완료", url=current_url)
                    await browser.close()
                    return {
                        "success": False,
                        "error": "LOGIN_INCOMPLETE",
                        "message": "로그인이 완료되지 않았습니다.",
                    }

            await browser.close()

            return {
                "success": True,
                "cookies": cookies,
                "message": "로그인 성공",
            }

        except PlaywrightTimeout:
            log.error("네트워크 타임아웃")
            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "login_error_timeout.png"))
            await browser.close()
            return {
                "success": False,
                "error": "TIMEOUT",
                "message": "네트워크 타임아웃이 발생했습니다.",
            }

        except Exception as e:
            log.error("알 수 없는 오류", error=str(e))
            if debug:
                await page.screenshot(path=str(DEBUG_DIR / "login_error_unknown.png"))
            await browser.close()
            return {
                "success": False,
                "error": "UNKNOWN_ERROR",
                "message": str(e),
            }


@router.post("/login")
async def login(request: Request, body: LoginRequest):
    """네이버 로그인 API"""

    client_ip = request.client.host if request.client else "unknown"

    # Rate limit 체크
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=429,
            detail="요청이 너무 많습니다. 1분 후 다시 시도해주세요.",
        )

    # 로그인 수행 (디버그 모드 ON)
    log.header("네이버 로그인", "🔐")
    log.kv("ID", f"{body.id[:3]}***")

    result = await naver_login_with_playwright(
        account_id=body.id,
        password=body.password,
        debug=True,
    )

    if result["success"]:
        log.success("로그인 성공", cookies=len(result.get("cookies", [])))
    else:
        log.error(f"로그인 실패: {result.get('error')}", message=result.get("message"))

    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": result.get("error"),
                "message": result.get("message"),
            },
        )

    # 세션 생성
    session_id = str(uuid.uuid4())
    sessions[session_id] = SessionData(
        cookies=result["cookies"],
        created_at=datetime.now(),
    )

    return JSONResponse(
        content={
            "success": True,
            "sessionId": session_id,
            "cookies": result["cookies"],
            "message": result["message"],
        }
    )


@router.post("/logout")
async def logout(body: LogoutRequest):
    """네이버 로그아웃 API"""

    session_id = body.sessionId

    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

    # 세션 삭제
    del sessions[session_id]

    return JSONResponse(
        content={
            "success": True,
            "message": "로그아웃 성공",
        }
    )


@router.get("/status")
async def status(sessionId: Optional[str] = None):
    """세션 상태 확인 API"""

    if not sessionId:
        raise HTTPException(status_code=400, detail="sessionId가 필요합니다.")

    if sessionId not in sessions:
        return JSONResponse(
            content={
                "valid": False,
                "message": "세션이 존재하지 않습니다.",
            }
        )

    session = sessions[sessionId]
    session.last_used = datetime.now()

    # 세션 만료 체크 (24시간)
    if datetime.now() - session.created_at > timedelta(hours=24):
        del sessions[sessionId]
        return JSONResponse(
            content={
                "valid": False,
                "message": "세션이 만료되었습니다.",
            }
        )

    return JSONResponse(
        content={
            "valid": True,
            "createdAt": session.created_at.isoformat(),
            "lastUsed": session.last_used.isoformat(),
            "cookieCount": len(session.cookies),
        }
    )


@router.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "ok", "service": "naver-auth-proxy"}
