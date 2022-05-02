from typing import Iterator
from unittest import mock

import pytest

import anime_metadata.providers.shinden
import anime_metadata.interfaces.cache


@pytest.fixture(scope="session")
def shinden_base_web_url(wiremock_url: str) -> str:
    return f"{wiremock_url}/shinden"


@pytest.fixture(scope="session")
def shinden_provider() -> anime_metadata.providers.shinden.ShindenProvider:
    return anime_metadata.providers.shinden.ShindenProvider(api_key="")


@pytest.fixture(autouse=True)
def _mock_shinden(shinden_base_web_url: str) -> Iterator[None]:
    with \
         mock.patch.object(anime_metadata.providers.shinden, "BASE_WEB_URL", shinden_base_web_url), \
         mock.patch.object(anime_metadata.providers.shinden, "MAX_SEARCH_PAGES", 3):
        yield
