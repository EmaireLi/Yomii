"""
作文双模型评测集成测试
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
async def test_app(monkeypatch: pytest.MonkeyPatch):
    from app.main import app
    from app.core import deps
    from app.api.v1.endpoints import essays as essays_endpoint

    async def fake_score(*, content: str, topic: str, target_level: str):
        class Result:
            model_version = "score-test-v1"
            payload = {
                "overall_score": 82,
                "task_completion_score": 84,
                "grammar_score": 80,
                "vocabulary_score": 81,
                "coherence_score": 83,
                "naturalness_score": 79,
                "jlpt_fit_score": 82,
                "level_estimate": target_level,
                "summary": f"围绕 {topic} 完成度较好。",
                "comments": "评分测试评论",
                "ai_evaluated": True,
            }

        return Result()

    async def fake_revision(*, content: str, topic: str, target_level: str, score_report: dict):
        class Result:
            model_version = "revision-test-v1"
            payload = {
                "issues": [
                    {
                        "source": content[:20],
                        "suggestion": content[:20],
                        "explanation": "建议补充连接词。",
                        "severity": "medium",
                    }
                ],
                "sentence_suggestions": [
                    {
                        "original": content[:20],
                        "suggested": f"また、{content[:20]}",
                        "reason": "使表达更连贯。",
                    }
                ],
                "full_revision": f"また、{content}",
                "revision_notes": f"{target_level} 目标下建议增强连贯性。",
            }

        return Result()

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    app.dependency_overrides[deps.get_dict_db] = get_test_session
    app.dependency_overrides[deps.get_user_db] = get_test_session
    monkeypatch.setattr(essays_endpoint, "ESSAY_TASK_SESSION_MAKER", test_session_maker)
    monkeypatch.setattr(
        essays_endpoint.essay_orchestrator_service.scoring_service,
        "evaluate_essay",
        fake_score,
    )
    monkeypatch.setattr(
        essays_endpoint.essay_orchestrator_service.revision_service,
        "revise_essay",
        fake_revision,
    )

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
async def test_essay_submit_report_and_history(client: AsyncClient):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "essay-user@example.com",
            "username": "essay_user",
            "password": "password123",
        },
    )
    assert register_response.status_code == 200

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "essay_user",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    submit_response = await client.post(
        "/api/v1/essays/submit",
        headers=headers,
        json={
            "title": "daily-life",
            "topic": "daily-life",
            "content": "私は毎朝日本語を勉強します。作文を書く練習も続けています。",
            "word_count": 31,
            "target_level": "N3",
        },
    )
    assert submit_response.status_code == 200
    essay = submit_response.json()
    assert essay["status"] in {"pending", "completed"}
    essay_id = essay["id"]

    report_response = await client.get(f"/api/v1/essays/{essay_id}/report", headers=headers)
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["status"] == "completed"
    assert report["scoreReport"]["overallScore"] == 82
    assert report["scoreReport"]["grammarScore"] == 80
    assert report["revisionReport"]["fullRevision"].startswith("また、")
    assert report["modelVersions"]["score"] == "score-test-v1"
    assert report["modelVersions"]["revision"] == "revision-test-v1"

    history_response = await client.get("/api/v1/essays/history?limit=10", headers=headers)
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 1
    assert history[0]["status"] == "completed"
    assert history[0]["scoreReport"]["overallScore"] == 82
    assert history[0]["revisionReport"]["fullRevision"].startswith("また、")

    score_response = await client.get(f"/api/v1/essays/{essay_id}/score", headers=headers)
    assert score_response.status_code == 200
    score_payload = score_response.json()
    assert score_payload["overallScore"] == 82
    assert score_payload["taskCompletionScore"] == 84
