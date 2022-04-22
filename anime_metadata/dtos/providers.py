from decimal import Decimal
from typing import Union, List

import attr

from . import show

__all__ = (
    "ProviderSeriesData",
)


@attr.s(auto_attribs=True, kw_only=True, frozen=True)
class ProviderSeriesData:
    id: str
    dates: show.ShowDate
    images: show.ShowImage
    plot: str
    rating: Union[Decimal, None] = attr.ib(converter=attr.converters.optional(lambda value: Decimal(str(value))))
    actors: List[show.ShowActor] = []
    staff: show.ShowStaff
    titles: show.ShowTitle
