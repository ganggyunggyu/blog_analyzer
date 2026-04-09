"""
네이버 블로그 예약글 체크 및 전화번호 없는 글 삭제 스크립트

사용법:
    python scripts/check_blog_reservations.py
    python scripts/check_blog_reservations.py --dry-run     # 삭제 없이 확인만
    python scripts/check_blog_reservations.py --group "도그마루 글밥"  # 특정 그룹만
"""

import json
import re
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser

ACCOUNTS_PATH = Path(__file__).parent / "blog_accounts.json"
PHONE_PATTERN = re.compile(r"0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}")

NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"
BLOG_MANAGE_URL = "https://blog.naver.com/PostManageList.naver?blogId={blog_id}&categoryNo=0&currentPage=1&countPerPage=10&publishType=6"


def load_accounts(group_filter: str | None = None) -> list[dict]:
    if not ACCOUNTS_PATH.exists():
        raise FileNotFoundError(
            f"계정 파일이 없음: {ACCOUNTS_PATH}\n"
            "blog_accounts.json을 생성하고 계정 정보를 입력하세요."
        )

    with open(ACCOUNTS_PATH, encoding="utf-8") as f:
        accounts = json.load(f)

    if group_filter:
        accounts = [a for a in accounts if a.get("group") == group_filter]

    return accounts


def naver_login(page: Page, username: str, password: str) -> bool:
    page.goto(NAVER_LOGIN_URL)
    page.wait_for_load_state("networkidle")

    page.click("#id")
    page.keyboard.type(username, delay=50)
    time.sleep(0.3)

    page.click("#pw")
    page.keyboard.type(password, delay=50)
    time.sleep(0.3)

    page.click(".btn_login")
    time.sleep(2)

    if "nidlogin" in page.url:
        print(f"  ❌ 로그인 실패 (캡챠 또는 잘못된 자격증명)")
        return False

    print(f"  ✅ 로그인 성공")
    return True


def get_reserved_posts(page: Page, blog_id: str) -> list[dict]:
    url = BLOG_MANAGE_URL.format(blog_id=blog_id)
    page.goto(url)
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    posts = []

    rows = page.query_selector_all("tr.item_row, tr._item")
    if not rows:
        rows = page.query_selector_all("table tbody tr")

    for row in rows:
        try:
            title_el = row.query_selector("a.title, td.title a, .post_title a")
            if not title_el:
                continue

            title = title_el.inner_text().strip()
            href = title_el.get_attribute("href") or ""

            checkbox = row.query_selector("input[type='checkbox']")
            post_id = checkbox.get_attribute("value") if checkbox else ""

            posts.append({
                "title": title,
                "href": href,
                "post_id": post_id,
                "row": row,
            })
        except Exception:
            continue

    return posts


def check_phone_in_post(page: Page, post_url: str) -> bool:
    page.goto(post_url)
    page.wait_for_load_state("networkidle")
    time.sleep(1)

    content = page.inner_text("body")
    return bool(PHONE_PATTERN.search(content))


def delete_post(page: Page, blog_id: str, post_id: str) -> bool:
    try:
        delete_url = f"https://blog.naver.com/PostDeleteForm.naver?blogId={blog_id}&logNo={post_id}"
        page.goto(delete_url)
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        confirm_btn = page.query_selector("a.btn_ok, button.btn_ok, #okButton")
        if confirm_btn:
            confirm_btn.click()
            time.sleep(1)
            return True
    except Exception as e:
        print(f"    삭제 실패: {e}")
    return False


def process_account(
    browser: Browser,
    account: dict,
    dry_run: bool = False,
) -> dict:
    nickname = account["nickname"]
    username = account["username"]
    password = account["password"]
    group = account.get("group", "")

    print(f"\n{'='*50}")
    print(f"📌 {nickname} ({username}) [{group}]")
    print(f"{'='*50}")

    if password in ("여기에_비밀번호_입력", ""):
        print("  ⚠️  비밀번호가 설정되지 않음 — 건너뜀")
        return {"nickname": nickname, "status": "skipped", "reason": "no_password"}

    context = browser.new_context()
    page = context.new_page()

    result = {
        "nickname": nickname,
        "username": username,
        "group": group,
        "reserved_count": 0,
        "no_phone_count": 0,
        "deleted_count": 0,
        "posts": [],
    }

    try:
        if not naver_login(page, username, password):
            result["status"] = "login_failed"
            return result

        posts = get_reserved_posts(page, username)
        result["reserved_count"] = len(posts)
        print(f"  📝 예약글 {len(posts)}개 발견")

        if not posts:
            result["status"] = "no_reserved_posts"
            return result

        for post in posts:
            post_url = post["href"]
            if not post_url.startswith("http"):
                post_url = f"https://blog.naver.com{post_url}"

            has_phone = check_phone_in_post(page, post_url)

            post_info = {
                "title": post["title"],
                "post_id": post["post_id"],
                "has_phone": has_phone,
                "deleted": False,
            }

            if not has_phone:
                result["no_phone_count"] += 1
                if dry_run:
                    print(f"    🔍 [DRY RUN] 전화번호 없음 → {post['title']}")
                else:
                    success = delete_post(page, username, post["post_id"])
                    post_info["deleted"] = success
                    result["deleted_count"] += int(success)
                    status_icon = "🗑️" if success else "❌"
                    print(f"    {status_icon} 전화번호 없음 → {post['title']}")
            else:
                print(f"    ✅ 전화번호 있음 → {post['title']}")

            result["posts"].append(post_info)

        result["status"] = "done"

    except Exception as e:
        print(f"  ❌ 오류: {e}")
        result["status"] = f"error: {e}"
    finally:
        context.close()

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="네이버 블로그 예약글 체크")
    parser.add_argument("--dry-run", action="store_true", help="삭제 없이 확인만")
    parser.add_argument("--group", type=str, help="특정 그룹만 처리")
    parser.add_argument("--headless", action="store_true", help="헤드리스 모드")
    args = parser.parse_args()

    accounts = load_accounts(group_filter=args.group)
    print(f"총 {len(accounts)}개 계정 처리 예정")

    if args.dry_run:
        print("🔍 DRY RUN 모드 — 삭제하지 않고 확인만 합니다")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)

        for account in accounts:
            result = process_account(browser, account, dry_run=args.dry_run)
            results.append(result)
            time.sleep(1)

        browser.close()

    print(f"\n{'='*50}")
    print("📊 최종 결과")
    print(f"{'='*50}")

    for r in results:
        status = r.get("status", "unknown")
        nickname = r["nickname"]

        if status == "skipped":
            print(f"  ⚠️  {nickname}: 건너뜀")
        elif status == "login_failed":
            print(f"  ❌ {nickname}: 로그인 실패")
        elif status == "no_reserved_posts":
            print(f"  📭 {nickname}: 예약글 없음")
        elif status == "done":
            print(
                f"  ✅ {nickname}: "
                f"예약글 {r['reserved_count']}개, "
                f"전화번호 없음 {r['no_phone_count']}개, "
                f"삭제 {r['deleted_count']}개"
            )
        else:
            print(f"  ❌ {nickname}: {status}")


if __name__ == "__main__":
    main()
