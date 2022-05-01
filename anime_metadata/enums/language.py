import enum

import babelfish

__all__ = [
    "Language",
]

_japanese = babelfish.Language("jpn")
_japanese.alpha2 = "jp"

_romaji = babelfish.Language("jpn")
_romaji.__setstate__(("x-jat", None, None))
_romaji.alpha2 = _romaji.alpha3


class Language(enum.Enum):
    ENGLISH = babelfish.Language("eng")
    JAPANESE = _japanese
    ROMAJI = _romaji
    UNKNOWN = ""
