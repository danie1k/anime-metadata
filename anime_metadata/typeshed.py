from typing import Any, Dict, NamedTuple, Set, Union

from typing_extensions import OrderedDict, TypedDict

AnimeId = Union[int, str]
AnimeTitle = str
CharacterId = Union[int, str]

TvShowId = Union[int, str]

CharacterName = str
PersonName = str
PositionName = str

EpisodeId = Union[int, str]
EpisodeNumber = int
EpisodeTitle = str

ApiResponseDataDict = Dict[str, Any]
ApiResponseDataObj = NamedTuple
ApiResponseData = Union[ApiResponseDataDict, ApiResponseDataObj]

CharacterList = OrderedDict[CharacterName, PersonName]
StaffList = Dict[PositionName, Set[PersonName]]

RawHtml = bytes

Iso8601DateStr = str
Iso8601DateTimeStr = str

Language = str


class RawCharacter(TypedDict, total=False):
    name_en: CharacterName
    name_jp_jp: CharacterName
    name_jp_romanized: CharacterName
    seiyuu: Dict[Language, Set[PersonName]]


class RawEpisode(TypedDict, total=False):
    id: EpisodeId
    no: EpisodeNumber
    plot: str
    premiered: str
    rating: str
    title_en: EpisodeTitle
    title_jp: EpisodeTitle
    title_jp_jp: EpisodeTitle
    title_jp_romanized: EpisodeTitle
