from typing import List

from typing_extensions import TypedDict

from anime_metadata.typeshed import AnimeTitle


class SearchResultItem(TypedDict):
    id: str  # int
    image_count: str  # int
    link: str
    poster: str
    title: str
    type: str


class ImageData(TypedDict):
    id: str  # int
    url: str
    lang: str  # two-letter code
    likes: str  # int


class TvData(TypedDict):
    hdclearart: List[ImageData]
    hdtvlogo: List[ImageData]
    name: AnimeTitle
    seasonposter: List[ImageData]
    showbackground: List[ImageData]
    thetvdb_id: str  # int
    tvbanner: List[ImageData]
    tvposter: List[ImageData]
    tvthumb: List[ImageData]
