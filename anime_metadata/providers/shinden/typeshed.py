from typing_extensions import TypedDict


class SearchResult(TypedDict):
    id: str
    image: str
    rating: str
    status: str
    title: str
    total_episodes: int
    type: str
