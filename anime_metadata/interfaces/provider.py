from typing import Any, Optional

from furl import furl
import requests

from anime_metadata import dtos
from anime_metadata.exceptions import ProviderNoResultError, ValidationError
from anime_metadata.typeshed import AnimeId, AnimeTitle

__all__ = [
    "BaseProvider",
]


class BaseProvider:
    def _get_series_by_id(self, anime_id: AnimeId) -> dtos.TvSeriesData:
        raise NotImplementedError

    def _find_series_by_title(self, title: AnimeTitle, year: Optional[int]) -> dtos.TvSeriesData:
        raise NotImplementedError

    def get_series(self, anime_id: AnimeId) -> dtos.TvSeriesData:
        return self._get_series_by_id(anime_id)

    def search_series(
        self,
        en_title: Optional[AnimeTitle] = None,
        jp_title: Optional[AnimeTitle] = None,
        year: Optional[int] = None,
    ) -> dtos.TvSeriesData:
        if en_title is None and jp_title is None:
            raise ValidationError('At least one "title" argument is required!')

        for title in (en_title, jp_title):
            if title is None:
                continue
            try:
                return self._find_series_by_title(title, year)
            except ProviderNoResultError:
                continue

        raise ProviderNoResultError(
            f"Cannot find {self.__class__.__name__} for en_title={en_title} / jp_title={jp_title}"
        )

    def get_request(self, url: furl, *args: Any, **kwargs: Any) -> bytes:
        response = requests.get(url.tostr(), *args, **kwargs)
        response.raise_for_status()
        return response.content
