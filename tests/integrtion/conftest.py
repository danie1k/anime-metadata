from typing import Iterator
from unittest import mock

import pytest

import anime_metadata.interfaces.cache
from anime_metadata.exceptions import CacheDataNotFound


@pytest.fixture(autouse=True)
def _disable_cache() -> Iterator[None]:
    with \
         mock.patch.object(anime_metadata.interfaces.cache.BaseCache, "get", side_effect=CacheDataNotFound), \
         mock.patch.object(anime_metadata.interfaces.cache.BaseCache, "set"):
        yield
