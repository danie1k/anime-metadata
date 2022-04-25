import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Sequence, Union

import attr
from dateutil.parser import ParserError, parse as dateutil_parse
from furl import furl

from anime_metadata import utils

if TYPE_CHECKING:
    from anime_metadata.dtos.show import ShowDate

# Converters


def date_converter(value: Any) -> Union[datetime.date, None]:  # noqa: C901
    if isinstance(value, datetime.date):
        return value
    if value is None:
        return None
    if hasattr(value, "text"):
        value = value.text

    value = value.strip()

    if not value:
        return None

    try:
        return dateutil_parse(value).date()
    except ParserError:
        return None


def genres_converter(value: Any) -> Sequence[str]:
    if not value:
        return []
    return sorted(map(
        utils.capitalize,
        ["Anime", *(item for item in set(value))],
    ))


def rating_converter(value: Any) -> Union[Decimal, None]:
    return attr.converters.optional(lambda value: Decimal(str(value)))(value)


def studios_converter(value: Any) -> Sequence[str]:
    if not value:
        return []
    return sorted(set(value))


# Factories


def year_factory(self: "ShowDate") -> Union[int, None]:
    if isinstance(self.premiered, datetime.date):
        return self.premiered.year
    return None


def image_url_factory(base_url: str, image_url: Union[str, None]) -> Union[str, None]:
    value = None if image_url is None else image_url.strip()
    if not value:
        return None

    if base_url:
        url = furl(base_url)
        url.path.add(value)
        return url.tostr()
    return value
