import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine , select
from models.Users import  User      
@pytest.fixture
def test_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False} , poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    print("TABLES CREATED:", SQLModel.metadata.tables.keys())  
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

from fastapi.testclient import TestClient
from main import app
from database import get_session

@pytest.fixture
def client(test_session):
    def override_test_session():
       yield test_session
    app.dependency_overrides[get_session] = override_test_session
    yield TestClient(app)
    app.dependency_overrides.clear()