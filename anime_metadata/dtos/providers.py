from decimal import Decimal
from typing import Any, Dict, Optional, Sequence, Set

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
    dates: Optional[show.ShowDate] = None
    genres: Optional[Set[str]] = attr.ib(default=None, converter=_utils.genres_converter)
    id: AnimeId
    images: Optional[show.ShowImage] = None
    main_characters: Optional[Set[show.ShowCharacter]] = attr.ib(default=None, converter=attr.converters.optional(set))
    mpaa: Optional[enums.MPAA] = None
    plot: Optional[str] = None
    rating: Optional[Decimal] = attr.ib(default=None, converter=_utils.rating_converter)
    secondary_characters: Optional[Set[show.ShowCharacter]] = attr.ib(
        default=None, converter=attr.converters.optional(set)
    )
    source_material: Optional[enums.SourceMaterial] = None
    staff: Optional[show.ShowStaff] = None
    studios: Optional[Set[str]] = attr.ib(default=None, converter=attr.converters.optional(set))
    titles: Dict[enums.Language, AnimeTitle]
    # #type: enums.ShowType = enums.ShowType.TV


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class TvSeriesData(ProviderData):
    episodes: Optional[Sequence[show.ShowEpisode]] = None
