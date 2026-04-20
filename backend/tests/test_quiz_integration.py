"""
测试模块集成测试：历史记录与能力报告
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

from app.models.word import Word

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

    app.dependency_overrides[deps.get_dict_db] = get_test_session
    app.dependency_overrides[deps.get_user_db] = get_test_session

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
async def test_quiz_session_history_and_report(client: AsyncClient):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "quiz-user@example.com",
            "username": "quiz_user",
            "password": "password123",
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["success"] is True

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "quiz_user",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    async with test_session_maker() as session:
        words = [
            Word(
                word="勉強",
                kana="べんきょう",
                japanese_meaning="学ぶこと",
                chinese_meaning="学习",
                example="毎日勉強します。",
            ),
            Word(
                word="世界",
                kana="せかい",
                japanese_meaning="地球全体",
                chinese_meaning="世界",
                example="世界は広い。",
            ),
            Word(
                word="家族",
                kana="かぞく",
                japanese_meaning="同じ家で生活する人",
                chinese_meaning="家人",
                example="家族と旅行する。",
            ),
            Word(
                word="仕事",
                kana="しごと",
                japanese_meaning="職業として行う業務",
                chinese_meaning="工作",
                example="仕事を始める。",
            ),
        ]
        session.add_all(words)
        await session.commit()

    questions_response = await client.get(
        "/api/v1/quiz/questions?difficulty=medium&count=3",
        headers=headers,
    )
    assert questions_response.status_code == 200
    questions = questions_response.json()
    assert len(questions) == 3
    assert "question" in questions[0]
    assert "options" in questions[0]

    first_question_id = int(questions[0]["id"])
    submit_response = await client.post(
        "/api/v1/quiz/session",
        headers=headers,
        json={
            "difficulty": "medium",
            "total_questions": 3,
            "correct_answers": 2,
            "duration_seconds": 120,
            "answers": [
                {"question_id": first_question_id, "user_answer": "A", "is_correct": True},
                {"question_id": first_question_id + 1, "user_answer": "B", "is_correct": True},
                {"question_id": first_question_id + 2, "user_answer": "C", "is_correct": False},
            ],
        },
    )
    assert submit_response.status_code == 200
    payload = submit_response.json()
    assert payload["success"] is True
    assert payload["session"]["totalQuestions"] == 3
    assert payload["report"]["historyCount"] >= 1
    assert payload["report"]["overallScore"] >= 0

    history_response = await client.get("/api/v1/quiz/history?limit=10", headers=headers)
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) >= 1
    assert history[0]["difficulty"] == "medium"
    assert history[0]["accuracy"] == pytest.approx(66.7, rel=1e-2)

    report_response = await client.get("/api/v1/quiz/report?limit=20", headers=headers)
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["historyCount"] >= 1
    assert "recommendations" in report
    assert report["level"] != ""
