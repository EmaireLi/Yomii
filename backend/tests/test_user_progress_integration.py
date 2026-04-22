"""
用户学习进度集成测试
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
async def test_app():
    from app.main import app
    from app.core import deps

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

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
async def test_progress_update_can_change_status(client: AsyncClient):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "progress-user@example.com",
            "username": "progress_user",
            "password": "password123",
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["success"] is True

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "progress_user",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.post(
        "/api/v1/user/progress/101",
        headers=headers,
        json={"word_id": 101, "status": "fuzzy", "is_correct": False},
    )
    assert first.status_code == 200
    assert first.json()["status"] == "fuzzy"
    assert first.json()["reviewCount"] == 1
    assert first.json()["correctCount"] == 0

    second = await client.post(
        "/api/v1/user/progress/101",
        headers=headers,
        json={"word_id": 101, "status": "known", "is_correct": True},
    )
    assert second.status_code == 200
    assert second.json()["status"] == "known"
    assert second.json()["reviewCount"] == 2
    assert second.json()["correctCount"] == 1

    progress_list = await client.get("/api/v1/user/progress", headers=headers)
    assert progress_list.status_code == 200
    payload = progress_list.json()
    assert len(payload) == 1
    assert payload[0]["wordId"] == "101"
    assert payload[0]["status"] == "known"
    assert payload[0]["reviewCount"] == 2
    assert payload[0]["correctCount"] == 1
