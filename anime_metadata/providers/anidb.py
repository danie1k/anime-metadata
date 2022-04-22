import datetime
import re
import xml.etree.ElementTree as ET
from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Optional, Union, Dict, List

import requests
from furl import furl
from rapidfuzz.distance import Indel

import anime_metadata.dtos.show
from anime_metadata import interfaces, dtos, models, utils, enums
from anime_metadata.exceptions import ProviderMultipleResultError

__all__ = (
    "AniDBProvider",
)

ANIDB_XML_NS = "{http://www.w3.org/XML/1998/namespace}"


class AniDBProvider(interfaces.BaseProvider):
    _cache_provider_ = "anidb"

    def __init__(self, anime_titles_file: Path, title_similarity_factor: float = 0.9) -> None:
        # https://wiki.anidb.net/API#Anime_Titles
        self.anime_titles_db = tuple(anime_titles_file.read_text().splitlines())
        self.title_similarity_factor = title_similarity_factor
        super().__init__()

    def _get_series_by_id(self, _id: str) -> dtos.ProviderSeriesData:
        _cache_data_type_ = "httpapi,anime"

        _cache = models.ProviderCache.get(self._cache_provider_, _id, _cache_data_type_)
        if _cache:
            return _xml_data_to_dto(ET.fromstring(_cache.decode("utf-8")))

        # https://wiki.anidb.net/HTTP_API_Definition
        url = furl("http://api.anidb.net:9001/httpapi")
        url.set({
            "aid": _id,
            "client": "mediabrowser",
            "clientver": 1,
            "protover": 1,
            "request": "anime",
        })

        response = requests.get(url.tostr())

        response.raise_for_status()
        if response.content.startswith(b"<error"):
            raise requests.HTTPError(response.content.decode(), response=response)

        models.ProviderCache.set(self._cache_provider_, _id, _cache_data_type_, response.content)

        return _xml_data_to_dto(ET.fromstring(response.text))

    def _search_series_by_title(self, title: str, year: Optional[int]) -> dtos.ProviderSeriesData:
        results = []

        for dbitem in self.anime_titles_db:
            if dbitem.startswith("#"):
                continue

            anidb_id, _, lang, dbtitle = dbitem.split("|", 3)

            cmp = Indel.normalized_similarity(dbtitle, title)
            if cmp == 1.0:
                return self._get_series_by_id(anidb_id)

            if cmp >= self.title_similarity_factor:
                results.append((cmp, anidb_id, lang, dbtitle))

        # TODO: Handle multiple results
        raise ProviderMultipleResultError


def _xml_data_to_dto(xml_root: ET.Element) -> dtos.ProviderSeriesData:
    parser = AniDBXML(xml_root)

    _titles = parser.get_titles()
    _main_staff = parser.get_main_staff()
    _characters = parser.get_characters()
    _episodes = parser.get_episodes()

    return dtos.ProviderSeriesData(
        id=str(xml_root.attrib["id"]),
        images=anime_metadata.dtos.show.ShowImage(
            base_url="https://cdn-eu.anidb.net/images/main/",
            folder=utils.normalize_string(xml_root.find("./picture"))
        ),
        titles=anime_metadata.dtos.show.ShowTitle(
            en=_titles["en"],
            jp_jp=_titles["jp_jp"],
            jp_romanized=_titles["jp_romanized"],
        ),
        dates=anime_metadata.dtos.show.ShowDate(
            premiered=parser.get_date("startdate"),
            ended=parser.get_date("enddate"),
        ),
        plot=utils.normalize_string(xml_root.find("./description")),
        rating=getattr(xml_root.find("./ratings/permanent"), "text", None),
        staff=anime_metadata.dtos.show.ShowStaff(
            director=collect_staff(_main_staff, "direction", "director"),
            music=collect_staff(_main_staff, "music"),
            screenwriter=collect_staff(_main_staff, "composition")
        ),
        actors=[
            anime_metadata.dtos.show.ShowActor(name=seiyuu, role=name)
            for name, seiyuu in list(_characters["main"].items()) + list(_characters["supporting"].items())
        ]
    )


def collect_staff(main_staff: Dict[str, List[str]], *needles: str) -> List[str]:
    result = set()

    for position_type, names in main_staff.items():
        for needle in needles:
            if needle.lower() in position_type.lower():
                result.update(names)

    return sorted(result)


class AniDBXML:
    def __init__(self, xml_root: ET.Element) -> None:
        self.xml_root = xml_root
        super().__init__()

    def get_date(self, date_name: str) -> Union[datetime.date, None]:
        result = self.xml_root.find(f"./{date_name}")
        if result is None:
            return None
        return datetime.date.fromisoformat(result.text.strip())

    def get_characters(self) -> Dict[str, Dict[str, str]]:
        result = {
            "main": {},
            "supporting": {},
        }

        for item in self.xml_root.findall("./characters/character"):
            name = getattr(item.find("./name"), "text", "").strip()
            seiyuu = getattr(item.find("./seiyuu"), "text", "").strip()

            if not (name and seiyuu):
                continue

            if "main character" in item.attrib["type"]:
                result["main"][name] = utils.reverse_name_order(seiyuu)
            if "secondary cast" in item.attrib["type"]:
                result["supporting"][name] = utils.reverse_name_order(seiyuu)

        return {
            "main": OrderedDict(sorted(result["main"].items())),
            "supporting": OrderedDict(sorted(result["supporting"].items())),
        }

    def get_episodes(self) -> Dict[enums.ShowEpisodeType, List[dict]]:
        result = {
            enums.ShowEpisodeType.REGULAR: [],
            enums.ShowEpisodeType.SPECIAL: [],
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

            ep = {
                "no": no,
                "airdate": getattr(item.find("./airdate"), "text", None),
                "id": item.attrib.get("id"),
                "plot": utils.normalize_string(item.find("./summary")),
                "rating": getattr(item.find("./rating"), "text", None),
                "titles": self.get_titles(item),
            }

            if _type == 1:
                result[enums.ShowEpisodeType.REGULAR].append(ep)
            elif _type == 2:
                result[enums.ShowEpisodeType.SPECIAL].append(ep)

        return {
            enums.ShowEpisodeType.REGULAR: sorted(
                result[enums.ShowEpisodeType.REGULAR], key=lambda item: (item["no"], item["airdate"])
            ),
            enums.ShowEpisodeType.SPECIAL: sorted(
                result[enums.ShowEpisodeType.SPECIAL], key=lambda item: (item["no"], item["airdate"])
            ),
        }

    def get_main_staff(self) -> Dict[str, List[str]]:
        results = defaultdict(list)

        for item in self.xml_root.findall("./creators/name"):
            results[item.attrib["type"]].append(utils.reverse_name_order(item.text))

        return results

    def get_titles(self, elem: ET.Element = None) -> Dict[str, str]:
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
