import datetime
import re
import xml.etree.ElementTree as ET
from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Optional, Union, Dict, List, NamedTuple, cast, Sequence, Set

import requests
from furl import furl
from rapidfuzz.distance import Indel

from anime_metadata import interfaces, dtos, models, utils, enums
from anime_metadata.exceptions import ProviderMultipleResultError, ProviderNoResultError, ProviderResultFound, \
    CacheDataNotFound
from anime_metadata.typeshed import AnimeTitle, AnimeId, RawHtml, StaffList, Iso8601DateTimeStr, Iso8601DateStr, \
    RawEpisode, CharacterList

__all__ = (
    "AniDBProvider",
)

ANIDB_XML_NS = "{http://www.w3.org/XML/1998/namespace}"

class DatRow(NamedTuple):
    aid: AnimeId
    type: str # 1=primary title (one per anime), 2=synonyms (multiple per anime), 3=shorttitles (multiple per anime), 4=official title (one per language)
    language: str
    title: AnimeTitle


class Cache(interfaces.BaseCache):
    provider_name = "anidb"


# TODO: Add web scraping

class AniDBProvider(interfaces.BaseProvider):
    def __init__(
        self,
        api_client_name: str,
        api_client_version: int,
        anime_titles_file: Path,
        title_similarity_factor: float = 0.9,
    ) -> None:
        self.api_client_name = api_client_name
        self.api_client_version = api_client_version
        # https://wiki.anidb.net/API#Anime_Titles
        self.anime_titles_db = tuple(
            DatRow(*dbitem.split("|", 3))
            for dbitem in anime_titles_file.read_text().splitlines()
            if not dbitem.startswith("#")
        )
        self.title_similarity_factor = title_similarity_factor
        super().__init__()

    def _find_series_by_title(self, title: AnimeTitle, year: Optional[int]) -> dtos.ProviderSeriesData:
        try:
            utils.find_title_in_provider_results(
                title=title,
                data=self.anime_titles_db,
                data_item_title_getter=lambda item: cast(DatRow, item).title,
                title_similarity_factor=self.title_similarity_factor,
            )
        except ProviderResultFound as exc:
            return self._get_series_by_id(cast(DatRow, exc.data_item).aid)

    def _get_series_by_id(self, anime_id: AnimeId) -> dtos.ProviderSeriesData:
        with Cache("httpapi,anime", anime_id) as cache:
            try:
                raw_xml_doc = cache.get()
            except CacheDataNotFound:
                # https://wiki.anidb.net/HTTP_API_Definition
                url = furl("http://api.anidb.net:9001/httpapi")
                url.set({
                    "aid": anime_id,
                    "client": self.api_client_name,
                    "clientver": self.api_client_version,
                    "protover": 1,
                    "request": "anime",
                })
                raw_xml_doc = self.get_request(url)
                if raw_xml_doc.startswith(b"<error"):
                    raise requests.HTTPError(raw_xml_doc.decode("utf-8"))

        return _xml_data_to_dto(raw_xml_doc)


def _xml_data_to_dto(raw_xml_doc: RawHtml) -> dtos.ProviderSeriesData:
    parser = AniDBXML(raw_xml_doc)

    characters = parser.get_characters()
    episodes = parser.get_episodes()
    main_staff = parser.get_main_staff()
    titles = parser.get_titles()

    return dtos.ProviderSeriesData(
        # ID
        id=parser.get_id(),
        # TODO: actors=[
        #         dtos.ShowActor(name=seiyuu, role=name)
        #         for name, seiyuu in list(_characters["main"].items()) + list(_characters["supporting"].items())
        #     ]
        # )
        # DATES
        dates=dtos.ShowDate(
            premiered=parser.get_date("startdate"),
            ended=parser.get_date("enddate"),
        ),
        # TODO: EPISODES
        episodes=raw_episodes_list_to_dtos(episodes, enums.EpisodeType.REGULAR),
        # TODO: GENRES
        genres=None,
        # IMAGES
        images=dtos.ShowImage(
            base_url="https://cdn-eu.anidb.net/images/main/",
            folder=parser.get_picture()
        ),
        # TODO: MPAA
        mpaa=None,
        # PLOT
        plot=parser.get_plot(),
        # RATING
        rating=parser.get_rating(),
        # TODO: SOURCE MATERIAL
        source_material=None,
        # STAFF
        staff=dtos.ShowStaff(
            director=utils.collect_staff(main_staff, "direction", "director"),
            music=utils.collect_staff(main_staff, "music"),
            screenwriter=utils.collect_staff(main_staff, "composition")
        ),
        # TODO: STUDIOS
        studios=None,
        # TITLES
        titles=dtos.ShowTitle(
            en=titles["en"],
            jp_jp=titles["jp_jp"],
            jp_romanized=titles["jp_romanized"],
        ),
    )


class AniDBXML:
    def __init__(self, raw_xml_doc: RawHtml) -> None:
        self.xml_root = ET.fromstring(raw_xml_doc)
        super().__init__()

    def get_characters(self) -> Dict[enums.CharacterType, CharacterList]:
        main_characters = {}
        supporting_characters = {}

        for item in self.xml_root.findall("./characters/character"):
            name = getattr(item.find("./name"), "text", "").strip()
            seiyuu = getattr(item.find("./seiyuu"), "text", "").strip()

            if not (name and seiyuu):
                continue

            if "main character" in item.attrib["type"]:
                main_characters[name] = utils.reverse_name_order(seiyuu)
            if "secondary cast" in item.attrib["type"]:
                supporting_characters[name] = utils.reverse_name_order(seiyuu)

        return {
            enums.CharacterType.MAIN: OrderedDict(sorted(main_characters.items())),
            enums.CharacterType.SUPPORTING: OrderedDict(sorted(supporting_characters.items())),
        }

    def get_date(self, date_name: str) -> Union[Iso8601DateStr, Iso8601DateTimeStr, None]:
        result = self.xml_root.find(f"./{date_name}")
        if result is None:
            return None
        return result.text.strip()

    def get_episodes(self) -> Dict[enums.EpisodeType, Sequence[RawEpisode]]:
        result = {
            enums.EpisodeType.REGULAR: [],
            enums.EpisodeType.SPECIAL: [],
        }

        for item in self.xml_root.findall("./episodes/episode"):
            _epno = item.find("./epno")
            # 1 = regular, 2 = Special (& OVA?), 3 = Opening/Ending, 4 = Trailer/Promo
            _type = int(_epno.attrib["type"])

            if _type not in (1, 2):
                continue

            no = int(re.search(r"(\d+)", _epno.text).group(1))
            if not no:
                continue

            ep: RawEpisode = {
                "id": item.attrib.get("id"),  # type:ignore
                "no": no,
            }

            airdate = getattr(item.find("./airdate"), "text", None)
            if airdate:
                ep["premiered"] = airdate

            plot = utils.normalize_string(item.find("./summary"))
            if plot:
                ep["plot"] = plot

            rating = getattr(item.find("./rating"), "text", None)
            if rating:
                ep["rating"] = rating

            titles = self.get_titles(item)
            if "en" in titles:
                ep["title_en"] = titles["en"]
            if "jp_jp" in titles:
                ep["title_jp_jp"] = titles["jp_jp"]
            if "jp_romanized" in titles:
                ep["title_jp_romanized"] = titles["jp_romanized"]

            if _type == 1:
                result[enums.EpisodeType.REGULAR].append(ep)
            elif _type == 2:
                result[enums.EpisodeType.SPECIAL].append(ep)

        return {
            enums.EpisodeType.REGULAR: sorted(
                result[enums.EpisodeType.REGULAR], key=lambda item: (int(item["no"]), item.get("airdate"))
            ),
            enums.EpisodeType.SPECIAL: sorted(
                result[enums.EpisodeType.SPECIAL], key=lambda item: (int(item["no"]), item.get("airdate"))
            ),
        }

    def get_id(self) -> AnimeId:
        return self.xml_root.attrib["id"]

    def get_main_staff(self) -> StaffList:
        results = defaultdict(set)

        for item in self.xml_root.findall("./creators/name"):
            results[item.attrib["type"]].add(utils.reverse_name_order(item.text))

        return results

    def get_picture(self) -> str:
        return utils.normalize_string(self.xml_root.find("./picture"))

    def get_plot(self) -> str:
        return utils.normalize_string(self.xml_root.find("./description"))

    def get_rating(self) -> Optional[str]:
        return getattr(self.xml_root.find("./ratings/permanent"), "text", None)

    def get_titles(self, elem: ET.Element = None) -> Dict[str, AnimeTitle]:
        elem = elem or self.xml_root.find("./titles")

        results = {
            "en": {},
            "x-jat": {},
            "ja": {},
        }

        for item in elem.findall("./title"):
            _lang = item.attrib[f"{ANIDB_XML_NS}lang"]
            _type = item.attrib.get("type", "main")

            if _lang not in ("x-jat", "en", "ja"):
                continue
            if _type not in ("main", "official"):
                continue

            results[_lang].setdefault(_type, item.text.rstrip("."))

        return {
            "en": utils.normalize_string(
                results["en"].get("main", results["en"].get("official"))
            ),
            "jp_jp": utils.normalize_string(
                results["ja"].get("main", results["ja"].get("official"))
            ),
            "jp_romanized": utils.normalize_string(
                results["x-jat"].get("main", results["x-jat"].get("official"))
            ),
        }


def raw_episodes_list_to_dtos(
    episodes_list: Dict[enums.EpisodeType, Sequence[RawEpisode]],
    _type: enums.EpisodeType,
) -> Sequence[dtos.ShowEpisode]:
    if not episodes_list.get(_type):
        return []

    result = []

    for ep_data in episodes_list[_type]:
        result.append(dtos.ShowEpisode(
            id=ep_data["id"],
            no=ep_data["no"],
            plot=ep_data.get("plot"),
            premiered=ep_data.get("premiered"),
            rating=ep_data.get("rating"),
            titles=dtos.ShowTitle(
                en=ep_data.get("title_en"),
                jp_jp=ep_data.get("title_jp_jp"),
                jp_romanized=ep_data.get("title_jp_romanized"),
            ),
            type=_type,
        ))

    return result