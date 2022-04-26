from collections.abc import Generator, Iterator
import re
from typing import Callable, Iterable, List, Union
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from lxml import html
from rapidfuzz.distance import Indel

from anime_metadata.exceptions import ProviderMultipleResultError, ProviderNoResultError, ProviderResultFound
from anime_metadata.typeshed import AnimeTitle, ApiResponseData, StaffList

ANIDB_LINK_REMOVER = re.compile(r"https?://(www\.)?anidb\.net/[^\s]+\s\[([^\]]+)\]")


def find_title_in_provider_results(  # noqa: C901
    title: AnimeTitle,
    data: Iterable[ApiResponseData],
    data_item_title_getter: Callable[[ApiResponseData], AnimeTitle],
    title_similarity_factor: float,
) -> None:
    if not isinstance(data, (Generator, Iterator)):
        if len(data) == 0:  # type:ignore
            raise ProviderNoResultError

        if len(data) == 1:  # type:ignore
            raise ProviderResultFound(data[0])  # type:ignore

    results = []

    for item in data:
        item_title = data_item_title_getter(item)
        cmp = Indel.normalized_similarity(item_title, title)
        if cmp == 1.0:
            raise ProviderResultFound(item)
        if cmp >= title_similarity_factor:
            results.append(item)

    if len(results) == 0:
        raise ProviderNoResultError

    if len(results) == 1:
        raise ProviderResultFound(results[0])

    # TODO: Handle multiple results
    raise ProviderMultipleResultError


def capitalize(value: str) -> str:
    return " ".join(map(str.capitalize, value.strip().split()))


def collect_staff(main_staff: StaffList, *needles: str) -> List[str]:
    result = set()

    for position_type, names in main_staff.items():
        for needle in needles:
            if needle.lower() in position_type.lower():
                result.update(names)

    return sorted(result)


def reverse_name_order(value: str) -> str:
    value = value.replace(",", "")
    return " ".join(list(filter(bool, map(str.strip, value.split())))[::-1])


def minimize_html(html: str) -> str:
    """
    Remove distracting whitespaces and newline characters
    """
    pat = re.compile(r"(^[\s]+)|([\s]+$)", re.MULTILINE)
    html = re.sub(pat, "", html)  # remove leading and trailing whitespaces
    html = re.sub("\n", " ", html)  # convert newlines to spaces
    # this preserves newline delimiters
    html = re.sub(r"[\s]+<", "<", html)  # remove whitespaces before opening tags
    html = re.sub(r">[\s]+", ">", html)  # remove whitespaces after closing tags
    return html


def load_html(raw_data: bytes) -> html.HtmlElement:
    return html.fromstring(str(BeautifulSoup(minimize_html(raw_data.decode("utf-8")), "html.parser")))


def normalize_string(value: Union[str, ET.Element, None]) -> Union[str, None]:
    value = getattr(getattr, "text", value)
    value = None if value is None else value.strip()
    if not value:
        return None

    result = (
        value.replace("`", "'")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("…", "...")
        .replace("—", "-")
        .replace('."', '".')
        .replace(',"', '",')
        .replace(';"', '";')
    )

    result = re.sub(r" {2,}", " ", result)
    result = ANIDB_LINK_REMOVER.sub("\\2", result)

    # TODO: Remove:
    #  - Text containing: "(Source ...)"

    def _line_filter(value: str) -> bool:
        value = value.strip()
        if value.lower().startswith("source:") or value.lower().startswith("note:"):
            return False
        return bool(value)

    # fmt: off
    result = "\n".join(
        filter(
            _line_filter,
            (line.strip("*").strip() for line in result.splitlines()),
        )
    )
    # fmt: on
    return result
