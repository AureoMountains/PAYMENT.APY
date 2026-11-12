import os

os.environ.setdefault("API_TOKEN", "test-secret-token")

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'test_payments.db'}"

    application = create_app(
        database_url=database_url,
        api_token="test-secret-token"
    )

    with TestClient(application) as test_client:
        yield test_client


@pytest.fixture
def headers():
    return {
        "X-Token": "test-secret-token"
    }
