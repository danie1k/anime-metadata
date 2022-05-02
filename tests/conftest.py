import os

import pytest
import requests


@pytest.fixture(scope="session")
def wiremock_url() -> str:
    return f"http://localhost:{os.environ['WIREMOCK_PORT']}"  # FIXME


@pytest.fixture(autouse=True, scope="session")
def _reload_wiremock_stubs(wiremock_url: str) -> None:
    response = requests.post(f"{wiremock_url}/__admin/mappings/reset")
    response.raise_for_status()
