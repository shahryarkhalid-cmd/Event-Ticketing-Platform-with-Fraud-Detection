import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine, select
from models.Users import User
from unittest.mock import patch, MagicMock


@pytest.fixture
def test_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    print("TABLES CREATED:", SQLModel.metadata.tables.keys())
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


from fastapi.testclient import TestClient
from main import app
from database import get_session


@pytest.fixture(autouse=True, scope="session")
def _fake_redis():
    import fakeredis
    import core.redis_client as _rc
    import services.Order_services as _os

    fake = fakeredis.FakeRedis(decode_responses=True)
    _rc.redis_client = fake
    _os.redis_client = fake


@pytest.fixture
def client(test_session):
    def override_test_session():
        yield test_session
    app.dependency_overrides[get_session] = override_test_session
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------- Shared mock for Supabase Storage ----------

@pytest.fixture
def mock_supabase_upload():
    """
    Patches the supabase client's storage calls in every service module
    that imports it, so tests never hit the real network or a real bucket.
    """
    with patch("services.Banner_services.supabase") as mock_banner_client, \
         patch("services.User_services.supabase") as mock_user_client:

        for mock_client in (mock_banner_client, mock_user_client):
            mock_bucket = MagicMock()
            mock_client.storage.from_.return_value = mock_bucket
            mock_bucket.upload.return_value = {"path": "fake/path.jpg"}
            mock_bucket.get_public_url.return_value = "https://fake.supabase.co/storage/v1/object/public/fake/path.jpg"
            mock_bucket.remove.return_value = None

        yield mock_banner_client
        
@pytest.fixture(autouse=True)
def mock_email_sending():
    with patch("services.Verification_service.send_verification_email") as mock_send:
        mock_send.return_value = None
        yield mock_send
        

@pytest.fixture(autouse=True, scope="session")
def _fake_redis():
    import fakeredis
    import core.redis_client as _rc
    import services.Order_services as _os
    import services.Verification_service as _vs   # <-- add this

    fake = fakeredis.FakeRedis(decode_responses=True)
    _rc.redis_client = fake
    _os.redis_client = fake
    _vs.redis_client = fake                        # <-- add this