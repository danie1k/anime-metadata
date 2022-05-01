from typing import Any, Dict, NamedTuple, Set, Union

import babelfish
from typing_extensions import OrderedDict, TypedDict

from anime_metadata import enums

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


class RawCharacter(TypedDict):
    name: Dict[enums.Language, CharacterName]
    seiyuu: Dict[babelfish.Language, Set[PersonName]]


class RawEpisode(TypedDict, total=False):
    id: EpisodeId
    no: EpisodeNumber
    plot: str
    premiered: str
    rating: str
    titles: Dict[enums.Language, AnimeTitle]
