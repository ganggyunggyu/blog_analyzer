import asyncio

from utils import llm_concurrency


def test_is_llm_path_matches_generate_routes_only() -> None:
    assert llm_concurrency.is_llm_path("/generate/blog-filler-pet")
    assert llm_concurrency.is_llm_path("/generate/alibaba")
    assert not llm_concurrency.is_llm_path("/search/all")
    assert not llm_concurrency.is_llm_path("/docs")


def test_run_with_llm_concurrency_limit_serializes_when_limit_is_one() -> None:
    async def exercise_limit() -> tuple[list[str], int]:
        llm_concurrency.llm_semaphore = asyncio.Semaphore(1)
        events: list[str] = []
        active = 0
        max_active = 0

        async def fake_operation(label: str) -> str:
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            events.append(f"start:{label}")
            await asyncio.sleep(0.01)
            events.append(f"end:{label}")
            active -= 1
            return label

        first, second = await asyncio.gather(
            llm_concurrency.run_with_llm_concurrency_limit(
                lambda: fake_operation("first")
            ),
            llm_concurrency.run_with_llm_concurrency_limit(
                lambda: fake_operation("second")
            ),
        )

        assert (first, second) == ("first", "second")
        return events, max_active

    events, max_active = asyncio.run(exercise_limit())

    assert max_active == 1
    assert events == [
        "start:first",
        "end:first",
        "start:second",
        "end:second",
    ]
