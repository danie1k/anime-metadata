from typing import Optional

from anime_metadata import dtos
from anime_metadata.exceptions import ValidationError, ProviderNoResultError

__all__ = (
    "BaseProvider",
)


class BaseProvider:

    def _get_series_by_id(self, _id: str) -> dtos.ProviderSeriesData:
        raise NotImplementedError

    def _search_series_by_title(self, title: str, year: Optional[int]) -> dtos.ProviderSeriesData:
        raise NotImplementedError

    def get_series(self, _id: str) -> dtos.ProviderSeriesData:
        return self._get_series_by_id(_id)

    def search_series(
        self,
        en_title: Optional[str] = None,
        jp_title: Optional[str] = None,
        year: Optional[int] = None,
    ) -> dtos.ProviderSeriesData:
        if en_title is None and jp_title is None:
            raise ValidationError('At least one "title" argument is required!')

        for title in (en_title, jp_title):
            if title is None:
                continue
            try:
                return self._search_series_by_title(title, year)
            except ProviderNoResultError:
                continue

        raise ProviderNoResultError(
            f'Cannot find {self.__class__.__name__} for en_title={en_title} / jp_title={jp_title}'
        )
