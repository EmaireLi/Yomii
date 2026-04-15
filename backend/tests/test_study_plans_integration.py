"""
学习计划相关集成测试 (使用 SQLite 内存数据库)
"""
from typing import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.stats import StudyStats
from app.models.user import User
from app.models.word import Word, WordTag

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
            email="study-plan-user@example.com",
            username="study_plan_user",
            hashed_password="not_used_in_test",
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        session.add(StudyStats(user_id=test_user.id))
        await session.commit()

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


async def _seed_words() -> None:
    async with test_session_maker() as session:
        words = [
            Word(
                word="単語1",
                kana="たんご1",
                japanese_meaning="日本語の意味1",
                chinese_meaning="中文释义1",
                example="例文1",
            ),
            Word(
                word="単語2",
                kana="たんご2",
                japanese_meaning="日本語の意味2",
                chinese_meaning="中文释义2",
                example="例文2",
            ),
            Word(
                word="単語3",
                kana="たんご3",
                japanese_meaning="日本語の意味3",
                chinese_meaning="中文释义3",
                example="例文3",
            ),
            Word(
                word="単語4",
                kana="たんご4",
                japanese_meaning="日本語の意味4",
                chinese_meaning="中文释义4",
                example="例文4",
            ),
        ]
        session.add_all(words)
        await session.commit()

        for word in words:
            await session.refresh(word)
            session.add(WordTag(word_id=word.id, tag="N2"))
        await session.commit()


@pytest.mark.asyncio
async def test_get_current_study_plan_auto_create(client: AsyncClient):
    response = await client.get("/api/v1/study-plans/current")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "默认学习计划"
    assert data["dailyGoal"] == 10
    assert data["reviewRatio"] == 0.5
    assert data["dictionaryId"] == "common"
    assert data["isActive"] is True


@pytest.mark.asyncio
async def test_update_plan_and_get_learn_words(client: AsyncClient):
    await _seed_words()

    current_response = await client.get("/api/v1/study-plans/current")
    plan_id = current_response.json()["id"]

    update_response = await client.put(
        f"/api/v1/study-plans/{plan_id}",
        json={
            "daily_goal": 3,
            "review_ratio": 0.5,
            "dictionary_id": "jlpt2",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["dailyGoal"] == 3
    assert update_response.json()["dictionaryId"] == "jlpt2"

    learn_response = await client.get(f"/api/v1/study-plans/{plan_id}/learn-words")
    assert learn_response.status_code == 200
    words = learn_response.json()
    assert len(words) == 3
    assert all("japanese_meaning" in word for word in words)
    assert all("chinese_meaning" in word for word in words)


@pytest.mark.asyncio
async def test_save_session_and_get_review_words(client: AsyncClient):
    await _seed_words()

    current_response = await client.get("/api/v1/study-plans/current")
    plan_id = current_response.json()["id"]

    await client.put(
        f"/api/v1/study-plans/{plan_id}",
        json={"daily_goal": 4, "review_ratio": 0.5},
    )

    learn_response = await client.get(f"/api/v1/study-plans/{plan_id}/learn-words")
    words = learn_response.json()
    learned_word_ids = [str(word["id"]) for word in words[:3]]

    save_response = await client.post(
        f"/api/v1/study-plans/{plan_id}/sessions",
        json={
            "date": "2026-04-15",
            "learned_words": learned_word_ids,
            "reviewed_words": [],
            "known_count": 1,
            "fuzzy_count": 1,
            "unknown_count": 1,
        },
    )
    assert save_response.status_code == 200
    assert save_response.json()["date"] == "2026-04-15"

    review_response = await client.get(f"/api/v1/study-plans/{plan_id}/review-words")
    assert review_response.status_code == 200
    review_words = review_response.json()
    assert len(review_words) == 2

    sessions_response = await client.get(f"/api/v1/study-plans/{plan_id}/sessions")
    assert sessions_response.status_code == 200
    sessions = sessions_response.json()
    assert len(sessions) >= 1
    assert sessions[0]["sessionStats"]["knownCount"] >= 0
