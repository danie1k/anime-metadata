import xml.etree.ElementTree as ET
import re
from typing import Union

ANIDB_LINK_REMOVER = re.compile(r"https?://(www\.)?anidb\.net/[^\s]+\s\[([^\]]+)\]")


def reverse_name_order(value: str) -> str:
    value = value.replace(',', '')
    return ' '.join(list(filter(bool, map(str.strip, value.split())))[::-1])


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
