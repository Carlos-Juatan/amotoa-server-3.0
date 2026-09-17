import pytest
import pytest_asyncio
from httpx import AsyncClient
from typing import AsyncGenerator
from mongomock_motor import AsyncMongoMockClient

from src.main import create_app
from src.core.database import db_holder

app = create_app()

@pytest.fixture(scope="session")
def mock_db_client():
    client = AsyncMongoMockClient()
    return client

@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_db(mock_db_client):
    # Swap out the real database with the mock database
    db_holder.client = mock_db_client
    db_holder.db = mock_db_client.get_database("test_db")
    
    yield db_holder.db
    
    # Clean up between tests
    await db_holder.client.drop_database("test_db")

@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
