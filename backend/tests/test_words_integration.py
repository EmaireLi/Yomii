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
    """空词库搜索应返回空分页结果"""
    response = await client.get("/api/v1/words/search?q=不存在&limit=10")
    assert response.status_code == 200
    assert response.json() == {"words": [], "total": 0, "page": 1, "limit": 10}


@pytest.mark.asyncio
async def test_search_words_with_tags(client: AsyncClient):
    """搜索结果包含标签"""
    async with test_session_maker() as session:
        word = Word(
            word="勉強",
            kana="べんきょう",
            japanese_meaning="学ぶこと",
            chinese_meaning="学习",
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

    payload = response.json()
    assert payload["total"] == 1
    assert payload["page"] == 1
    assert payload["limit"] == 10
    assert len(payload["words"]) == 1
    assert payload["words"][0]["word"] == "勉強"
    assert payload["words"][0]["kana"] == "べんきょう"
    assert "N5" in payload["words"][0]["tags"]


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
async def test_search_words_pagination(client: AsyncClient):
    """搜索接口支持分页和自定义 limit"""
    async with test_session_maker() as session:
        words = [
            Word(
                word="勉強A",
                kana="べんきょうえー",
                japanese_meaning="学ぶことA",
                chinese_meaning="学习A",
                example="例句A",
            ),
            Word(
                word="勉強B",
                kana="べんきょうびー",
                japanese_meaning="学ぶことB",
                chinese_meaning="学习B",
                example="例句B",
            ),
            Word(
                word="勉強C",
                kana="べんきょうしー",
                japanese_meaning="学ぶことC",
                chinese_meaning="学习C",
                example="例句C",
            ),
        ]
        session.add_all(words)
        await session.commit()

    response = await client.get("/api/v1/words/search?q=勉強&page=2&limit=1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["page"] == 2
    assert payload["limit"] == 1
    assert len(payload["words"]) == 1


@pytest.mark.asyncio
async def test_search_words_priority_order(client: AsyncClient):
    """搜索结果优先级：word > chinese_meaning > japanese_meaning > kana"""
    keyword = "priority-key"
    async with test_session_maker() as session:
        words = [
            Word(
                word="かなのみ",
                kana=f"{keyword}-kana",
                japanese_meaning="仅假名命中",
                chinese_meaning="仅假名命中",
                example="例句1",
            ),
            Word(
                word="日文释义命中",
                kana="にほんご",
                japanese_meaning=f"{keyword} in japanese meaning",
                chinese_meaning="日文释义命中",
                example="例句2",
            ),
            Word(
                word="中文释义命中",
                kana="ちゅうぶん",
                japanese_meaning="中文释义命中",
                chinese_meaning=f"{keyword} 在中文释义",
                example="例句3",
            ),
            Word(
                word=f"{keyword}-word",
                kana="たんご",
                japanese_meaning="词条本体命中",
                chinese_meaning="词条本体命中",
                example="例句4",
            ),
        ]
        session.add_all(words)
        await session.commit()

    response = await client.get(f"/api/v1/words/search?q={keyword}&page=1&limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 4
    assert [item["word"] for item in payload["words"]] == [
        f"{keyword}-word",
        "中文释义命中",
        "日文释义命中",
        "かなのみ",
    ]


@pytest.mark.asyncio
async def test_search_words_exact_match_first(client: AsyncClient):
    """同字段内精确匹配应优先于包含匹配（例如 エロ 优先于 イエロー）"""
    async with test_session_maker() as session:
        words = [
            Word(
                word="イエロー",
                kana="いえろー",
                japanese_meaning="yellow",
                chinese_meaning="黄色",
                example="例句1",
            ),
            Word(
                word="エロ",
                kana="えろ",
                japanese_meaning="erotic",
                chinese_meaning="情色",
                example="例句2",
            ),
        ]
        session.add_all(words)
        await session.commit()

    response = await client.get("/api/v1/words/search?q=エロ&page=1&limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert [item["word"] for item in payload["words"]][:2] == ["エロ", "イエロー"]


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
            japanese_meaning="本を読む場所",
            chinese_meaning="图书馆",
            example="図書館で本を借りました。",
        )
        session.add(word)
        await session.commit()

    response = await client.get("/api/v1/words/search?q=図書館&limit=10", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["words"]) == 1

    history_response = await client.get("/api/v1/user/search-history?limit=10", headers=headers)
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) >= 1
    assert history[0]["keyword"] == "図書館"


@pytest.mark.asyncio
async def test_favorites_crud_for_authenticated_user(client: AsyncClient):
    """登录用户可添加、查看、移除收藏词汇"""
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "favorite-user@example.com",
            "username": "favorite_user",
            "password": "password123",
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["success"] is True

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "favorite_user",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    async with test_session_maker() as session:
        word = Word(
            word="猫",
            kana="ねこ",
            japanese_meaning="猫という動物",
            chinese_meaning="猫",
            example="猫が好きです。",
        )
        session.add(word)
        await session.commit()
        await session.refresh(word)
        session.add(WordTag(word_id=word.id, tag="N5"))
        await session.commit()

    add_response = await client.post(f"/api/v1/user/favorites/{word.id}", headers=headers)
    assert add_response.status_code == 200
    assert add_response.json()["success"] is True

    list_response = await client.get("/api/v1/user/favorites", headers=headers)
    assert list_response.status_code == 200
    favorites = list_response.json()
    assert len(favorites) == 1
    assert favorites[0]["word"] == "猫"
    assert favorites[0]["japanese_meaning"] == "猫という動物"
    assert favorites[0]["chinese_meaning"] == "猫"
    assert "N5" in favorites[0]["tags"]

    remove_response = await client.delete(f"/api/v1/user/favorites/{word.id}", headers=headers)
    assert remove_response.status_code == 200
    assert remove_response.json()["success"] is True

    empty_response = await client.get("/api/v1/user/favorites", headers=headers)
    assert empty_response.status_code == 200
    assert empty_response.json() == []


@pytest.mark.asyncio
async def test_favorites_search_and_pagination(client: AsyncClient):
    """收藏支持按时间倒序分页和关键词搜索"""
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "favorite-search-user@example.com",
            "username": "favorite_search_user",
            "password": "password123",
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["success"] is True

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "favorite_search_user",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    async with test_session_maker() as session:
        words = [
            Word(
                word="黄色",
                kana="きいろ",
                japanese_meaning="色の一つ",
                chinese_meaning="黄色",
                example="黄色い花",
            ),
            Word(
                word="猫",
                kana="ねこ",
                japanese_meaning="動物",
                chinese_meaning="猫",
                example="猫が寝る",
            ),
            Word(
                word="勉強",
                kana="べんきょう",
                japanese_meaning="学ぶこと",
                chinese_meaning="学习",
                example="日本語を勉強する",
            ),
        ]
        session.add_all(words)
        await session.commit()
        for word in words:
            await session.refresh(word)

    for word in words:
        add_response = await client.post(f"/api/v1/user/favorites/{word.id}", headers=headers)
        assert add_response.status_code == 200
        assert add_response.json()["success"] is True

    page1_response = await client.get("/api/v1/user/favorites/search?page=1&limit=2", headers=headers)
    assert page1_response.status_code == 200
    page1 = page1_response.json()
    assert page1["total"] == 3
    assert page1["page"] == 1
    assert page1["limit"] == 2
    assert [item["word"] for item in page1["words"]] == ["勉強", "猫"]

    page2_response = await client.get("/api/v1/user/favorites/search?page=2&limit=2", headers=headers)
    assert page2_response.status_code == 200
    page2 = page2_response.json()
    assert page2["total"] == 3
    assert page2["page"] == 2
    assert [item["word"] for item in page2["words"]] == ["黄色"]

    search_response = await client.get("/api/v1/user/favorites/search?q=学习&page=1&limit=10", headers=headers)
    assert search_response.status_code == 200
    searched = search_response.json()
    assert searched["total"] == 1
    assert [item["word"] for item in searched["words"]] == ["勉強"]
