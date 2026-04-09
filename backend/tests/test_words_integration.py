"""
单词搜索相关集成测试 (使用 SQLite 内存数据库)
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

    # 搜索接口会同时用到词典库和用户库依赖
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
async def test_search_words_empty(client: AsyncClient):
    """空词库搜索应返回空数组"""
    response = await client.get("/api/v1/words/search?q=不存在&limit=10")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_search_words_with_tags(client: AsyncClient):
    """搜索结果包含标签"""
    async with test_session_maker() as session:
        word = Word(
            word="勉強",
            kana="べんきょう",
            meaning="学习",
            example="毎日日本語を勉強します。",
            part_of_speech="名词",
        )
        session.add(word)
        await session.commit()
        await session.refresh(word)

        session.add(WordTag(word_id=word.id, tag="N5"))
        await session.commit()

    response = await client.get("/api/v1/words/search?q=勉強&limit=10")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["word"] == "勉強"
    assert data[0]["kana"] == "べんきょう"
    assert "N5" in data[0]["tags"]


@pytest.mark.asyncio
async def test_get_all_words_pagination(client: AsyncClient):
    """分页接口返回 total 和 words"""
    response = await client.get("/api/v1/words/?page=1&limit=20")
    assert response.status_code == 200
    data = response.json()
    assert "words" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["limit"] == 20


@pytest.mark.asyncio
async def test_search_writes_history_for_authenticated_user(client: AsyncClient):
    """登录用户搜索后应写入搜索历史"""
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "search-user@example.com",
            "username": "search_user",
            "password": "password123",
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["success"] is True

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "search_user",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    async with test_session_maker() as session:
        word = Word(
            word="図書館",
            kana="としょかん",
            meaning="图书馆",
            example="図書館で本を借りました。",
        )
        session.add(word)
        await session.commit()

    response = await client.get("/api/v1/words/search?q=図書館&limit=10", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1

    history_response = await client.get("/api/v1/user/search-history?limit=10", headers=headers)
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) >= 1
    assert history[0]["keyword"] == "図書館"
