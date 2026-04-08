"""
用户认证功能集成测试 (使用 SQLite 内存数据库)
"""
import pytest
import asyncio
from typing import AsyncGenerator

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# 配置测试数据库
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
    expire_on_commit=False
)


async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    """获取测试数据库会话"""
    async with test_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
async def test_app():
    """创建测试应用"""
    from app.main import app
    from app.core import deps
    from app.models.user import User
    from app.models.stats import StudyStats
    
    # 创建测试表
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # 覆盖数据库依赖
    app.dependency_overrides[deps.get_user_db] = get_test_session
    
    yield app
    
    # 清理
    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
async def client(test_app: FastAPI):
    """测试客户端"""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """测试用户注册成功"""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["message"] == "注册成功"
    assert "user_id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """测试重复邮箱注册失败"""
    # 第一次注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "username": "user1",
            "password": "password123"
        }
    )
    
    # 第二次注册（相同邮箱）
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "username": "user2",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "邮箱已被注册" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    """测试重复用户名注册失败"""
    # 第一次注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user1@example.com",
            "username": "sameuser",
            "password": "password123"
        }
    )
    
    # 第二次注册（相同用户名）
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user2@example.com",
            "username": "sameuser",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert "用户名已被使用" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """测试用户登录成功"""
    # 先注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "loginpassword123"
        }
    )
    
    # 使用用户名登录
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "loginuser",
            "password": "loginpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "loginuser"
    assert data["user"]["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_login_with_email(client: AsyncClient):
    """测试使用邮箱登录"""
    # 先注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "email@example.com",
            "username": "emailuser",
            "password": "password123"
        }
    )
    
    # 使用邮箱登录
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "email@example.com",  # 使用邮箱作为用户名
            "password": "password123"
        }
    )
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "email@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """测试错误密码登录失败"""
    # 先注册
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong@example.com",
            "username": "wronguser",
            "password": "correctpassword"
        }
    )
    
    # 使用错误密码登录
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "wronguser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "用户名或密码错误" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """测试不存在的用户登录失败"""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent",
            "password": "password123"
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """测试获取当前用户信息"""
    # 注册并登录
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "username": "meuser",
            "password": "mepassword123"
        }
    )
    
    login_response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "meuser",
            "password": "mepassword123"
        }
    )
    token = login_response.json()["access_token"]
    
    # 获取当前用户信息
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meuser"
    assert data["email"] == "me@example.com"
    assert data["is_active"] == True


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """测试无效令牌"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """测试未授权访问"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """测试登出"""
    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert response.json()["message"] == "登出成功"
