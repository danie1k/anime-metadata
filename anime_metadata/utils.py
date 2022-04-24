import re
from typing import Union, List, Callable
import xml.etree.ElementTree as ET

from rapidfuzz.distance import Indel

from anime_metadata.exceptions import ProviderNoResultError, ProviderResultFound, ProviderMultipleResultError
from anime_metadata.typeshed import StaffList, ApiResponseData, AnimeTitle

ANIDB_LINK_REMOVER = re.compile(r"https?://(www\.)?anidb\.net/[^\s]+\s\[([^\]]+)\]")


def find_title_in_provider_results(
    title: AnimeTitle,
    data: List[ApiResponseData],
    data_item_title_getter: Callable[[ApiResponseData], AnimeTitle],
    title_similarity_factor: float,
) -> None:
    if len(data) == 0:
        raise ProviderNoResultError

    if len(data) == 1:
        raise ProviderResultFound(data[0])

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
    value = value.replace(',', '')
    return ' '.join(list(filter(bool, map(str.strip, value.split())))[::-1])


def minimize_html(html: str) -> str:
    """
    Remove distracting whitespaces and newline characters
    """
    pat = re.compile('(^[\s]+)|([\s]+$)', re.MULTILINE)
    html = re.sub(pat, '', html)       # remove leading and trailing whitespaces
    html = re.sub('\n', ' ', html)     # convert newlines to spaces
    # this preserves newline delimiters
    html = re.sub('[\s]+<', '<', html) # remove whitespaces before opening tags
    html = re.sub('>[\s]+', '>', html) # remove whitespaces after closing tags
    return html


def normalize_string(value: Union[str, ET.Element, None]) -> Union[str, None]:
    if hasattr(value, "text"):
        value = value.text
    value = None if value is None else value.strip()
    if not value:
        return None

    result = (
        value
            .replace("`", "'")
            .replace("’", "'")
            .replace('“', '"')
            .replace('”', '"')
            .replace('…', '...')
            .replace('—', '-')
            .replace('."', '".')
            .replace(',"', '",')
            .replace(';"', '";')
    )

    result = re.sub(r' {2,}', ' ', result)
    result = ANIDB_LINK_REMOVER.sub('\\2', result)

    result = "\n".join(
        line.strip("*").strip() for line in result.splitlines()
    )

    return result
