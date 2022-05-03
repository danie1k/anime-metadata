import datetime
from decimal import Decimal
import string
from typing import TYPE_CHECKING, Any, List, Set, Union

import attr
from dateutil.parser import ParserError, parse as dateutil_parse
from furl import furl

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


def genres_converter(value: Any) -> Set[str]:
    if not value:
        return set()

    result = map(lambda item: string.capwords(item, " "), value)
    result = map(lambda item: string.capwords(item, "-"), result)
    return {"Anime", *result}


def rating_converter(value: Any) -> Union[Decimal, None]:
    return attr.converters.optional(lambda value: Decimal(str(value)))(value)


def unique_list_converter(value: Any) -> List[str]:
    if not value:
        return []
    return list(set(value))


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
        return furl(base_url).add(path=value).tostr()
    return value
