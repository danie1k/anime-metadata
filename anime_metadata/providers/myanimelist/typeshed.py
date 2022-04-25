from typing import Any, Dict, List, Union

from typing_extensions import TypedDict

from anime_metadata.typeshed import AnimeId, AnimeTitle, Iso8601DateStr, Iso8601DateTimeStr


class MALApiResponseData(TypedDict):
    alternative_titles: Dict[str, Union[AnimeTitle, List[AnimeTitle]]]
    average_episode_duration: int
    background: str
    broadcast: Dict[str, str]
    created_at: Iso8601DateTimeStr
    end_date: Iso8601DateStr
    genres: List[Dict[str, Union[int, str]]]
    id: AnimeId
    main_picture: Dict[str, str]
    mean: float
    media_type: str
    nsfw: str
    num_episodes: int
    num_list_users: int
    num_scoring_users: int
    pictures: List[Dict[str, str]]
    popularity: int
    rank: int
    rating: str
    recommendations: List[Dict[str, Any]]
    related_anime: List[Dict[str, Any]]
    related_manga: List[Dict[str, Any]]
    source: str
    start_date: Iso8601DateStr
    start_season: Dict[str, Union[int, str]]
    statistics: Dict[str, Any]
    status: str
    studios: List[Dict[str, Union[int, str]]]
    synopsis: str
    title: AnimeTitle
    updated_at: Iso8601DateTimeStr
