from decimal import Decimal
from typing import Any, Dict, Optional, Sequence

import attr

from anime_metadata import enums
from anime_metadata.typeshed import AnimeId, AnimeTitle

from . import _utils, show

__all__ = [
    "TvSeriesData",
]


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class ProviderData:
    _provider: object
    _raw: Optional[Dict[str, Any]] = None
    characters: Optional[Sequence[show.ShowCharacter]] = None
    dates: Optional[show.ShowDate] = None
    genres: Optional[Sequence[str]] = attr.ib(default=None, converter=_utils.genres_converter)
    id: AnimeId
    images: show.ShowImage
    mpaa: Optional[enums.MPAA] = None
    plot: Optional[str] = None
    rating: Optional[Decimal] = attr.ib(default=None, converter=_utils.rating_converter)
    source_material: Optional[enums.SourceMaterial] = None
    staff: Optional[show.ShowStaff] = None
    studios: Optional[Sequence[str]] = attr.ib(default=None, converter=_utils.unique_list_converter)
    titles: Dict[enums.Language, AnimeTitle]


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class TvSeriesData(ProviderData):
    episodes: Optional[Sequence[show.ShowEpisode]] = None
