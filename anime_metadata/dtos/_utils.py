import datetime
from typing import Any, Union, TYPE_CHECKING

from furl import furl

if TYPE_CHECKING:
    from anime_metadata.dtos.show import ShowDate


def date_converter(value: Any) -> Union[datetime.date, None]:
    if isinstance(value, datetime.date):
        return value
    if value is None:
        return None
    if hasattr(value, "text"):
        value = value.text

    value = value.strip()

    if not value:
        return None

    return datetime.date.fromisoformat(value)


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
