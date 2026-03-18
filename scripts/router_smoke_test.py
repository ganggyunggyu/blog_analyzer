from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi import APIRouter
from fastapi.testclient import TestClient

from routers.auth import blog_write
from routers.bot import router as bot_router
from routers.bot.common_models import QueueInfo
from routers.search import manage as search_manage


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def build_client(router: APIRouter) -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def check_api_route_registration() -> None:
    import importlib

    with patch("mongodb_service.MongoClient", return_value=MagicMock()):
        api_module = importlib.import_module("api")
        api_module = importlib.reload(api_module)

    route_paths = {route.path for route in api_module.app.routes}
    expected_paths = {
        "/blog/health",
        "/blog/write",
        "/search/manuscript/{manuscript_id}",
        "/search/manuscript/{manuscript_id}/visibility",
        "/search/manuscripts/visible",
        "/bot/health",
        "/bot/queues",
    }
    missing_paths = sorted(expected_paths - route_paths)
    assert_condition(not missing_paths, f"누락된 라우트: {missing_paths}")


def check_blog_router() -> None:
    client = build_client(blog_write.router)

    with patch(
        "routers.auth.blog_write.write_blog_post",
        new=AsyncMock(
            return_value={
                "success": True,
                "post_url": "https://example.com/post/1",
                "message": "글 발행 완료",
            }
        ),
    ) as mocked_write_blog_post:
        response = client.post(
            "/blog/write",
            json={
                "cookies": [],
                "title": "테스트 제목",
                "content": "테스트 본문",
                "tags": ["테스트"],
                "images": ["image.png"],
                "is_public": True,
            },
        )

    assert_condition(response.status_code == 200, f"/blog/write 실패: {response.text}")
    payload = response.json()
    assert_condition(payload["success"] is True, "/blog/write success 누락")
    assert_condition(payload["post_url"] == "https://example.com/post/1", "post_url 불일치")
    assert_condition(mocked_write_blog_post.await_count == 1, "write_blog_post 호출 누락")

    health_response = client.get("/blog/health")
    assert_condition(health_response.status_code == 200, "/blog/health 실패")
    assert_condition(
        health_response.json() == {"status": "ok", "service": "blog-write"},
        "/blog/health 응답 불일치",
    )


def check_search_router() -> None:
    client = build_client(search_manage.router)

    with (
        patch(
            "routers.search.manage.delete_manuscript_by_id",
            return_value={"ok": True, "deletedId": "abc123"},
        ),
        patch(
            "routers.search.manage.update_manuscript_by_id",
            return_value={
                "ok": True,
                "manuscript": {
                    "_id": "abc123",
                    "content": "수정됨",
                    "updatedAt": "2026-03-18T00:00:00",
                },
            },
        ),
        patch(
            "routers.search.manage.toggle_visibility_by_id",
            return_value={"ok": True, "visible": False, "manuscriptId": "abc123"},
        ),
        patch(
            "routers.search.manage.get_visible_manuscripts",
            return_value={
                "documents": [{"_id": "abc123", "__category": "테스트"}],
                "total": 1,
                "skip": 0,
                "limit": 20,
            },
        ),
    ):
        delete_response = client.delete(
            "/search/manuscript/abc123",
            params={"category": "테스트"},
        )
        update_response = client.patch(
            "/search/manuscript/abc123",
            params={"category": "테스트"},
            json={"content": "수정됨", "memo": "메모"},
        )
        visibility_response = client.patch(
            "/search/manuscript/abc123/visibility",
            params={"category": "테스트"},
        )
        visible_response = client.get(
            "/search/manuscripts/visible",
            params={"category": "테스트", "page": 1, "limit": 20},
        )

    assert_condition(delete_response.status_code == 200, f"DELETE 실패: {delete_response.text}")
    assert_condition(update_response.status_code == 200, f"PATCH 실패: {update_response.text}")
    assert_condition(
        visibility_response.status_code == 200,
        f"visibility 실패: {visibility_response.text}",
    )
    assert_condition(visible_response.status_code == 200, f"visible 실패: {visible_response.text}")
    assert_condition(delete_response.json()["deletedId"] == "abc123", "삭제 응답 불일치")
    assert_condition(update_response.json()["manuscript"]["content"] == "수정됨", "수정 응답 불일치")
    assert_condition(visibility_response.json()["visible"] is False, "노출 토글 응답 불일치")
    assert_condition(visible_response.json()["total"] == 1, "노출 목록 응답 불일치")


def check_bot_router() -> None:
    client = build_client(bot_router)

    with (
        patch(
            "routers.bot.health.get_manuscript_list",
            side_effect=[[1], [1, 2], [1, 2, 3]],
        ),
        patch(
            "routers.bot.queue.list_active_queues",
            return_value=[
                QueueInfo(
                    queue_id="queue_test_0318",
                    created_at="2026-03-18T00:00:00",
                    manuscript_count=2,
                    status="pending",
                )
            ],
        ),
    ):
        health_response = client.get("/bot/health")
        queues_response = client.get("/bot/queues")

    assert_condition(health_response.status_code == 200, f"/bot/health 실패: {health_response.text}")
    assert_condition(queues_response.status_code == 200, f"/bot/queues 실패: {queues_response.text}")
    assert_condition(
        health_response.json()["queue"] == {
            "pending": 1,
            "completed": 2,
            "failed": 3,
        },
        "/bot/health 응답 불일치",
    )
    assert_condition(queues_response.json()["count"] == 1, "/bot/queues count 불일치")


def run_check(name: str, check: Callable[[], None]) -> None:
    check()
    print(f"[OK] {name}")


def main() -> None:
    checks = [
        ("api-route-registration", check_api_route_registration),
        ("blog-router", check_blog_router),
        ("search-router", check_search_router),
        ("bot-router", check_bot_router),
    ]

    for name, check in checks:
        run_check(name, check)

    print("[DONE] router smoke tests passed")


if __name__ == "__main__":
    main()
