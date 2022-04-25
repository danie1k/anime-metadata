from typing import NamedTuple

from anime_metadata.typeshed import AnimeId, AnimeTitle


class DatRow(NamedTuple):
    aid: AnimeId
    type: str  # 1=primary title (one per anime), 2=synonyms (multiple per anime), 3=shorttitles (multiple per anime), 4=official title (one per language)
    language: str
    title: AnimeTitle
