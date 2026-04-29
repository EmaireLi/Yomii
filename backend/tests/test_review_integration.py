"""
复习调度接口集成测试
"""
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.progress import ProgressStatus, WordProgress
from app.models.user import User
from app.models.word import Word
from app.services.review_service import create_initial_progress

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine: AsyncEngine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

test_session_maker = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def test_app():
    from app.main import app
    from app.core import deps

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with test_session_maker() as session:
        test_user = User(
            email="review-user@example.com",
            username="review_user",
            hashed_password="not_used_in_test",
        )
        session.add(test_user)

        words = [
            Word(
                word="単語A",
                kana="たんごA",
                japanese_meaning="日本語の意味A",
                chinese_meaning="中文释义A",
                example="例文A",
            ),
            Word(
                word="単語B",
                kana="たんごB",
                japanese_meaning="日本語の意味B",
                chinese_meaning="中文释义B",
                example="例文B",
            ),
            Word(
                word="単語C",
                kana="たんごC",
                japanese_meaning="日本語の意味C",
                chinese_meaning="中文释义C",
                example="例文C",
            ),
        ]
        session.add_all(words)
        await session.commit()
        await session.refresh(test_user)
        for word in words:
            await session.refresh(word)

    async def get_test_current_user() -> User:
        return test_user

    app.dependency_overrides[deps.get_user_db] = get_test_session
    app.dependency_overrides[deps.get_dict_db] = get_test_session
    app.dependency_overrides[deps.get_current_active_user] = get_test_current_user

    yield app

    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def client(test_app: FastAPI):
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_post_review_updates_sm2_fields(client: AsyncClient):
    first = await client.post("/api/v1/review/1", json={"rating": "hard"})
    assert first.status_code == 200
    first_payload = first.json()["progress"]
    assert first_payload["status"] == "fuzzy"
    assert first_payload["reviewCount"] == 1
    assert 0.02 <= first_payload["interval"] <= 0.1
    assert first_payload["ease"] < 2.5

    second = await client.post("/api/v1/review/1", json={"rating": "good"})
    assert second.status_code == 200
    second_payload = second.json()["progress"]
    assert second_payload["status"] == "known"
    assert second_payload["reviewCount"] == 2
    assert second_payload["interval"] > first_payload["interval"]
    assert second_payload["interval"] <= 60.0
    assert second_payload["ease"] > first_payload["ease"]


@pytest.mark.asyncio
async def test_again_triggers_lapse_penalty_after_three_lapses(client: AsyncClient):
    for _ in range(3):
        response = await client.post("/api/v1/review/2", json={"rating": "again"})
        assert response.status_code == 200

    payload = response.json()["progress"]
    assert payload["lapseCount"] == 3
    assert payload["ease"] == 1.7


@pytest.mark.asyncio
async def test_get_review_today_returns_due_words_sorted(client: AsyncClient):
    now = datetime.utcnow()
    async with test_session_maker() as session:
        first = create_initial_progress(user_id=1, word_id=1, now=now - timedelta(days=2))
        second = create_initial_progress(user_id=1, word_id=2, now=now - timedelta(days=1))
        first.next_review = now - timedelta(minutes=30)
        second.next_review = now - timedelta(minutes=10)
        first.status = ProgressStatus.FUZZY
        second.status = ProgressStatus.UNKNOWN
        session.add(first)
        session.add(second)
        await session.commit()

    response = await client.get("/api/v1/review/today?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    items = payload["items"]
    assert len(items) == 2
    assert items[0]["progress"]["wordId"] == "1"
    assert items[1]["progress"]["wordId"] == "2"


@pytest.mark.asyncio
async def test_get_review_random_returns_weighted_items(client: AsyncClient):
    now = datetime.utcnow()
    async with test_session_maker() as session:
        rows = [
            create_initial_progress(user_id=1, word_id=1, now=now - timedelta(days=2)),
            create_initial_progress(user_id=1, word_id=2, now=now - timedelta(days=1)),
            create_initial_progress(user_id=1, word_id=3, now=now - timedelta(days=3)),
        ]
        rows[0].interval = 0.5
        rows[0].lapse_count = 2
        rows[0].ease = 1.4
        rows[1].interval = 5.0
        rows[1].lapse_count = 0
        rows[1].ease = 2.6
        rows[2].interval = 1.0
        rows[2].lapse_count = 1
        rows[2].ease = 2.0
        session.add_all(rows)
        await session.commit()

    response = await client.get("/api/v1/review/random?limit=2")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    assert len(payload["items"]) == 2
    for item in payload["items"]:
        assert "word" in item
        assert "progress" in item
        assert item["progress"]["wordId"] in {"1", "2", "3"}
