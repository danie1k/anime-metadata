from collections import OrderedDict, defaultdict
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Union, cast
import xml.etree.ElementTree as ET

from furl import furl
import requests

from anime_metadata import constants, dtos, enums, interfaces, utils
from anime_metadata.exceptions import CacheDataNotFound, ProviderResultFound
from anime_metadata.typeshed import (
    AnimeId,
    AnimeTitle,
    CharacterList,
    Iso8601DateStr,
    Iso8601DateTimeStr,
    RawEpisode,
    RawHtml,
    StaffList,
)

from .typeshed import DatRow

__all__ = [
    "AniDBProvider",
]

BASE_API_URL = "http://api.anidb.net:9001"
BASE_WEB_URL = "https://anidb.net"
BASE_IMG_CDN_URL = "https://cdn-eu.anidb.net/images/main"

LANG = {
    "en": enums.Language.ENGLISH,
    "ja": enums.Language.JAPANESE,
    "x-jat": enums.Language.ROMAJI,
}


class Cache(interfaces.BaseCache):
    provider_name = "anidb"


class AniDBProvider(interfaces.BaseProvider):
    def __init__(self, *args: Any, anime_titles_file: Path, **kwargs: Any) -> None:
        # https://wiki.anidb.net/API#Anime_Titles
        self.anime_titles_db = tuple(
            DatRow(*dbitem.split("|", 3))
            for dbitem in anime_titles_file.read_text().splitlines()
            if not dbitem.startswith("#")
        )
        super().__init__(*args, **kwargs)

    def _find_series_by_title(self, title: AnimeTitle, year: Optional[int]) -> dtos.TvSeriesData:
        try:
            utils.find_title_in_provider_results(
                title=title,
                data=self.anime_titles_db,
                data_item_title_getter=lambda item: cast(DatRow, item).title,
                title_similarity_factor=self.title_similarity_factor,
            )
        except ProviderResultFound as exc:
            return self._get_series_by_id(cast(DatRow, exc.data_item).aid)

        raise NotImplementedError

    def _get_series_by_id(self, anime_id: AnimeId) -> dtos.TvSeriesData:
        return _raw_data_to_dto(
            self._get_anime_from_api(anime_id),
            self._get_anime_from_web(anime_id),
        )

    # ------------------------------------------------------------------------------------------------------------------

    def _get_anime_from_api(self, anime_id: AnimeId) -> RawHtml:
        with Cache("httpapi,anime", anime_id) as cache:
            try:
                raw_xml_doc = cache.get()
            except CacheDataNotFound:
                # https://wiki.anidb.net/HTTP_API_Definition
                raw_xml_doc = self.get_request(
                    furl(
                        BASE_API_URL,
                        args={
                            "aid": anime_id,
                            "client": self.api_key.split("|")[0],
                            "clientver": self.api_key.split("|")[1],
                            "protover": 1,
                            "request": "anime",
                        },
                    ).add(path=["httpapi"])
                )
                if raw_xml_doc.startswith(b"<error"):
                    raise requests.HTTPError(raw_xml_doc.decode("utf-8"))

        return raw_xml_doc

    def _get_anime_from_web(self, anime_id: AnimeId) -> RawHtml:
        with Cache("web,anime", anime_id) as cache:
            try:
                raw_html_page = cache.get()
            except CacheDataNotFound:
                raw_html_page = self.get_request(
                    furl(BASE_WEB_URL).add(path=["anime", anime_id]),
                    headers={
                        "User-Agent": constants.USER_AGENT,
                        "Referer": BASE_WEB_URL,
                    },
                )
                cache.set(raw_html_page)

        return raw_html_page


def _raw_data_to_dto(raw_xml_doc: RawHtml, web_html_page: RawHtml) -> dtos.TvSeriesData:
    xml_parser = AniDBXML(raw_xml_doc)
    web_parser = AniDBWeb(anime_page=web_html_page)

    characters = xml_parser.get_characters()
    episodes = xml_parser.get_episodes()
    main_staff = xml_parser.get_main_staff()

    return dtos.TvSeriesData(
        provider=AniDBProvider,
        raw={"api": raw_xml_doc, "web": web_html_page},
        # ID
        id=xml_parser.get_id(),
        # CHARACTERS
        main_characters={
            dtos.ShowCharacter(name=name, seiyuu=seiyuu)  # type:ignore
            for name, seiyuu in characters[enums.CharacterType.MAIN].items()
        }
        or None,
        secondary_characters={
            dtos.ShowCharacter(name=name, seiyuu=seiyuu)  # type:ignore
            for name, seiyuu in characters[enums.CharacterType.SUPPORTING].items()
        }
        or None,
        # DATES
        dates=dtos.ShowDate(
            premiered=xml_parser.get_date("startdate"),
            ended=xml_parser.get_date("enddate"),
        ),
        # EPISODES
        episodes=raw_episodes_list_to_dtos(episodes, enums.EpisodeType.REGULAR, web_parser.extract_episodes_count()),
        # GENRES
        genres=web_parser.extract_tags_from_html(),
        # IMAGES
        images=dtos.ShowImage(
            base_url=BASE_IMG_CDN_URL,
            folder=xml_parser.get_picture(),
        ),
        # PLOT
        plot=xml_parser.get_plot(),
        # RATING
        rating=xml_parser.get_rating(),
        # SOURCE MATERIAL
        source_material=web_parser.extract_source_material(),
        # STAFF
        staff=dtos.ShowStaff(
            director=utils.collect_staff(main_staff, "direction", "director"),
            music=utils.collect_staff(main_staff, "music"),
            screenwriter=utils.collect_staff(main_staff, "composition"),
        ),
        # STUDIOS
        studios=map(utils.reverse_name_order, main_staff.get("Animation Work")),  # type:ignore
        # TITLES
        titles=xml_parser.get_titles(),
    )


class AniDBXML:
    NS = "{http://www.w3.org/XML/1998/namespace}"

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

    def get_episodes(self) -> Dict[enums.EpisodeType, Sequence[RawEpisode]]:  # noqa: C901
        result_regular = []
        result_special = []

        for item in self.xml_root.findall("./episodes/episode"):
            _epno = item.find("./epno")
            # 1 = regular, 2 = Special (& OVA?), 3 = Opening/Ending, 4 = Trailer/Promo
            _type = int(_epno.attrib["type"])

            if _type not in (1, 2):
                continue

            no = int(re.search(r"(\d+)", _epno.text).group(1))  # type:ignore
            if not no:
                continue

            ep: RawEpisode = {
                "id": item.attrib.get("id"),
                "no": no,
                "titles": self.get_titles(item),
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

            if _type == 1:
                result_regular.append(ep)
            elif _type == 2:
                result_special.append(ep)

        return {
            enums.EpisodeType.REGULAR: sorted(result_regular, key=lambda item: (int(item["no"]), item.get("airdate"))),
            enums.EpisodeType.SPECIAL: sorted(result_special, key=lambda item: (int(item["no"]), item.get("airdate"))),
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

    def get_titles(self, elem: ET.Element = None) -> Dict[enums.Language, AnimeTitle]:
        elem = elem or self.xml_root.find("./titles")

        results: Dict[enums.Language, Dict[str, AnimeTitle]] = defaultdict(dict)

        for item in elem.findall("./title"):
            _lang = item.attrib[f"{AniDBXML.NS}lang"]
            _type = item.attrib.get("type", "main")

            if _lang not in LANG.keys():
                continue
            if _type not in ("main", "official"):
                continue

            results[LANG[_lang]].setdefault(_type, item.text.rstrip("."))

        return {
            lang: utils.normalize_string(titles.get("main", titles.get("official"))) for lang, titles in results.items()
        }


class AniDBWeb:
    source_material_tags = {
        # https://anidb.net/tag/2609/animetb
        2609: "original work",
        4424: "American derived",
        7252: "CG collection",
        2800: "game",
        2798: "manga",
        6493: "manhua",
        5010: "manhwa",
        2796: "movie",
        2797: "new",
        2799: "novel",
        7469: "picture book",
        6453: "radio programme",
        6446: "television programme",
        3714: "Western animated cartoon",
        3430: "Western comics",
    }

    def __init__(self, *, anime_page: bytes = None) -> None:
        self.anime_page = anime_page
        super().__init__()

    def extract_episodes_count(self) -> int:
        if not self.anime_page:
            raise ValueError
        the_page = utils.load_html(self.anime_page)

        return int(the_page.xpath("//*[@itemprop='numberOfEpisodes']")[0].text.strip())

    def extract_source_material(self) -> enums.SourceMaterial:
        # fmt: off
        result = [
            item["name"]
            for item in self._get_all_tags()
            if item["id"] in self.source_material_tags.keys()
        ]
        # fmt: on
        if len(result) != 1:
            raise NotImplementedError

        _source = str(result[0]).lower()

        if "manga" in _source or _source in ["manhua", "manhwa"]:
            return enums.SourceMaterial.MANGA

        if "game" in _source:
            return enums.SourceMaterial.GAME

        if "novel" in _source:
            return enums.SourceMaterial.LIGHT_NOVEL

        if "original" in _source:
            return enums.SourceMaterial.ORIGINAL

        # return enums.SourceMaterial.OTHER
        raise NotImplementedError

    def extract_tags_from_html(self) -> Set[str]:
        # fmt: off
        return {
            cast(str, item["name"])
            for item in self._get_all_tags()
            if item["id"] not in self.source_material_tags.keys()
        }
        # fmt: on

    def _get_all_tags(self) -> List[Dict[str, Union[int, str]]]:
        if not self.anime_page:
            raise ValueError
        the_page = utils.load_html(self.anime_page)

        result = []
        for item in the_page.xpath("//span[contains(@class, 'tagname')][@itemprop='genre']"):
            result.append(
                {
                    "id": int(item.xpath("./ancestor::a[position()=1]")[0].attrib["href"].split("/")[2]),
                    "name": item.text.strip(),
                }
            )

        return result


def raw_episodes_list_to_dtos(  # noqa: C901
    episodes_list: Dict[enums.EpisodeType, Sequence[RawEpisode]],
    _type: enums.EpisodeType,
    total_episodes: int = None,
) -> Sequence[dtos.ShowEpisode]:
    if not episodes_list.get(_type):
        return []

    if total_episodes is not None:
        if total_episodes == 0:
            return []
        if len(episodes_list[_type]) != total_episodes:
            raise NotImplementedError

    result = []

    for ep_data in episodes_list[_type]:
        result.append(
            dtos.ShowEpisode(
                id=ep_data["id"],
                no=ep_data["no"],
                plot=ep_data.get("plot"),
                premiered=ep_data.get("premiered"),
                rating=ep_data.get("rating"),
                titles=ep_data["titles"],
                type=_type,
            )
        )

    if len(result) != total_episodes:
        raise NotImplementedError

    return result
