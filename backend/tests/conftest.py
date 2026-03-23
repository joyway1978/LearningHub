"""
Pytest Configuration and Fixtures

Provides test fixtures for database sessions, test client, and authentication.
Uses SQLite in-memory database for fast test execution.
"""

import os
import sys
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.material import Material, MaterialStatus, MaterialType, Like, View
from app.core.security import get_password_hash, create_access_token
from app.schemas.user import UserCreate


# Use SQLite in-memory database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    # Create engine
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign key support for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_2(db_session: Session) -> User:
    """Create a second test user."""
    user = User(
        email="test2@example.com",
        name="Test User 2",
        hashed_password=get_password_hash("testpassword456"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    """Create an access token for the test user."""
    return create_access_token(subject=test_user.id)


@pytest.fixture
def test_user_2_token(test_user_2: User) -> str:
    """Create an access token for the second test user."""
    return create_access_token(subject=test_user_2.id)


@pytest.fixture
def authorized_client(client: TestClient, test_user_token: str) -> TestClient:
    """Create an authorized test client with Bearer token."""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_user_token}"
    }
    return client


@pytest.fixture
def authorized_client_2(client: TestClient, test_user_2_token: str) -> TestClient:
    """Create an authorized test client for user 2 with Bearer token."""
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {test_user_2_token}"
    }
    return client


@pytest.fixture
def test_video_material(db_session: Session, test_user: User) -> Material:
    """Create a test video material."""
    material = Material(
        title="Test Video",
        description="A test video material",
        type=MaterialType.VIDEO,
        file_path="materials/1/20240101_000000_test.mp4",
        file_size=1024 * 1024,  # 1MB
        file_format="mp4",
        thumbnail_path="thumbnails/1/1.jpg",
        uploader_id=test_user.id,
        status=MaterialStatus.ACTIVE,
        view_count=10,
        like_count=5
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


@pytest.fixture
def test_pdf_material(db_session: Session, test_user: User) -> Material:
    """Create a test PDF material."""
    material = Material(
        title="Test PDF",
        description="A test PDF material",
        type=MaterialType.PDF,
        file_path="materials/1/20240101_000001_test.pdf",
        file_size=512 * 1024,  # 512KB
        file_format="pdf",
        thumbnail_path="thumbnails/1/2.jpg",
        uploader_id=test_user.id,
        status=MaterialStatus.ACTIVE,
        view_count=5,
        like_count=2
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


@pytest.fixture
def test_hidden_material(db_session: Session, test_user: User) -> Material:
    """Create a test hidden material."""
    material = Material(
        title="Hidden Material",
        description="A hidden test material",
        type=MaterialType.VIDEO,
        file_path="materials/1/20240101_000002_hidden.mp4",
        file_size=2048 * 1024,  # 2MB
        file_format="mp4",
        thumbnail_path=None,
        uploader_id=test_user.id,
        status=MaterialStatus.HIDDEN,
        view_count=0,
        like_count=0
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


@pytest.fixture
def test_processing_material(db_session: Session, test_user: User) -> Material:
    """Create a test processing material."""
    material = Material(
        title="Processing Material",
        description="A processing test material",
        type=MaterialType.PDF,
        file_path="materials/1/20240101_000003_processing.pdf",
        file_size=256 * 1024,  # 256KB
        file_format="pdf",
        thumbnail_path=None,
        uploader_id=test_user.id,
        status=MaterialStatus.PROCESSING,
        view_count=0,
        like_count=0
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


@pytest.fixture
def test_like(db_session: Session, test_user: User, test_video_material: Material) -> Like:
    """Create a test like."""
    like = Like(
        user_id=test_user.id,
        material_id=test_video_material.id
    )
    db_session.add(like)
    db_session.commit()
    db_session.refresh(like)
    return like
