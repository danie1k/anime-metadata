import os
from pathlib import Path
from typing import Iterator
from unittest import mock

import pytest

import anime_metadata.providers.anidb

CWD = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture(scope="session")
def anidb_anime_titles_file() -> Path:
    return Path(CWD) / "anidb-anime-titles.dat"


@pytest.fixture(scope="session")
def anidb_base_api_url(wiremock_url: str) -> str:
    return f"{wiremock_url}/anidb"


@pytest.fixture(scope="session")
def anidb_base_web_url(wiremock_url: str) -> str:
    return f"{wiremock_url}/anidb/web"


@pytest.fixture(scope="session")
def anidb_base_img_cdn_url(wiremock_url: str) -> str:
    return f"{wiremock_url}/anidb/images"


@pytest.fixture(scope="session")
def anidb_provider(anidb_anime_titles_file: Path) -> anime_metadata.providers.anidb.AniDBProvider:
    return anime_metadata.providers.anidb.AniDBProvider(
        api_key="client|clientver",
        anime_titles_file=anidb_anime_titles_file,
    )


@pytest.fixture(autouse=True)
def _mock_anidb(anidb_base_api_url: str, anidb_base_web_url: str, anidb_base_img_cdn_url: str) -> Iterator[None]:
    with \
        mock.patch.object(anime_metadata.providers.anidb, "BASE_API_URL", anidb_base_api_url), \
        mock.patch.object(anime_metadata.providers.anidb, "BASE_WEB_URL", anidb_base_web_url), \
        mock.patch.object(anime_metadata.providers.anidb, "BASE_IMG_CDN_URL", anidb_base_img_cdn_url):
        yield
