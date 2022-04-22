import datetime
from decimal import Decimal
from typing import Union, List

import attr

from anime_metadata import enums
from . import _utils

__all__ = (
    "ShowActor",
    "ShowDate",
    "ShowEpisode",
    "ShowImage",
    "ShowStaff",
    "ShowTitle",
)


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class ShowActor:
    name: str
    role: str


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class ShowStaff:
    director: List[str] = []
    guest_star: List[str] = []
    music: List[str] = []
    screenwriter: List[str] = []


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class ShowDate:
    premiered: Union[datetime.date, None] = attr.ib(converter=_utils.date_converter)
    ended: Union[datetime.date, None] = attr.ib(converter=_utils.date_converter)
    year: Union[int, None] = attr.ib(default=attr.Factory(_utils.year_factory, takes_self=True))


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class ShowImage:
    _base_url: Union[str, None] = None
    backdrop: Union[str, None] = None
    banner: Union[str, None] = None
    folder: Union[str, None] = None
    landscape: Union[str, None] = None
    logo: Union[str, None] = None

    def __attrs_post_init__(self) -> None:
        if not self._base_url:
            return
        for attrib in self.__attrs_attrs__:
            if not attrib.name.startswith("_"):
                object.__setattr__(
                    self,
                    attrib.name,
                    _utils.image_url_factory(self._base_url, getattr(self, attrib.name)),
                )


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class ShowTitle:
    en: str
    jp_jp: Union[str, None] = None
    jp_romanized: Union[str, None] = None

    @property
    def jp(self) -> Union[str, None]:
        if self.jp_romanized:
            return self.jp_romanized
        return self.jp_jp


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class ShowEpisode:

    no: int
    type: enums.ShowEpisodeType = enums.ShowEpisodeType.REGULAR

    id: str
    plot: str
    premiered: Union[datetime.date, None] = attr.ib(converter=_utils.date_converter)
    rating: Union[Decimal, None] = attr.ib(converter=attr.converters.optional(lambda value: Decimal(str(value))))
    titles: ShowTitle
