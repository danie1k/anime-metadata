from decimal import Decimal
from typing import Union, Sequence, Any, Optional

import attr

from anime_metadata import enums
from . import show, _utils

__all__ = (
    "TvSeriesData",
)


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class ProviderData:
    _raw: Optional[Any] = None
    characters: Sequence[show.ShowCharacter] = []
    dates: show.ShowDate
    genres: Sequence[str] = attr.ib(converter=_utils.genres_converter)
    id: str
    images: show.ShowImage
    mpaa: Union[enums.MPAA, None]
    plot: str
    rating: Union[Decimal, None] = attr.ib(converter=_utils.rating_converter)
    source_material: Union[enums.SourceMaterial, None]
    staff: show.ShowStaff
    studios: Sequence[str] = attr.ib(converter=_utils.studios_converter)
    titles: show.ShowTitle


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class TvSeriesData(ProviderData):
    episodes: Sequence[show.ShowEpisode]
