import collections
import json
from typing import Dict, List, Optional, Sequence, Set, cast

import babelfish
from furl import furl
from lxml.html import HtmlElement
from typing_extensions import OrderedDict

from anime_metadata import dtos, enums, interfaces, utils
from anime_metadata.exceptions import CacheDataNotFound, ProviderResultFound
from anime_metadata.typeshed import (
    AnimeId,
    AnimeTitle,
    ApiResponseDataDict,
    CharacterList,
    CharacterName,
    EpisodeNumber,
    RawCharacter,
    RawEpisode,
    StaffList,
)

from .typeshed import MALApiResponse

__all__ = [
    "MALProvider",
]


MAL_DATA = {
    "alternative_titles",
    "average_episode_duration",
    "background",
    "broadcast",
    "created_at",
    "end_date",
    "genres",
    "id",
    "main_picture",
    "mean",
    "media_type",
    # "my_list_status",
    "nsfw",
    "num_episodes",
    "num_list_users",
    "num_scoring_users",
    "pictures",
    "popularity",
    "rank",
    "rating",
    "recommendations",
    "related_anime",
    "related_manga",
    "source",
    "start_date",
    "start_season",
    "statistics",
    "status",
    "studios",
    "synopsis",
    "title",
    "updated_at",
}


class Cache(interfaces.BaseCache):
    provider_name = "mal"


class MALProvider(interfaces.BaseProvider):
    def _find_series_by_title(self, title: AnimeTitle, year: Optional[int]) -> dtos.TvSeriesData:
        url = furl("https://myanimelist.net/search/prefix.json")
        url.set(
            {
                "keyword": title,
                "type": "anime",
                "v": 1,
            }
        )

        response = self.get_request(
            url,
            headers={
                "Referer": "https://myanimelist.net/",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        json_data: ApiResponseDataDict = json.loads(response)

        try:
            utils.find_title_in_provider_results(
                title=title,
                data=json_data["categories"][0]["items"],
                data_item_title_getter=lambda item: cast(ApiResponseDataDict, item)["name"],
                title_similarity_factor=self.title_similarity_factor,
            )
        except ProviderResultFound as exc:
            data_item: ApiResponseDataDict = exc.data_item  # type:ignore
            return self._get_series_by_id(data_item["id"])

        raise NotImplementedError

    def _get_series_by_id(self, anime_id: AnimeId) -> dtos.TvSeriesData:
        characters_list = self._get_anime_characters_from_web(anime_id)

        return _raw_data_to_dto(
            episodes_list=self._get_anime_episodes_from_web(anime_id),
            main_characters=collections.OrderedDict(
                (character_name, self._get_character_from_web(character_id))
                for character_name, character_id in characters_list[enums.CharacterType.MAIN].items()
            ),
            mal_api_data=self._get_anime_from_api(anime_id),
            staff_list=self._get_anime_staff_from_web(anime_id),
            supporting_characters=collections.OrderedDict(
                (character_name, self._get_character_from_web(character_id))
                for character_name, character_id in characters_list[enums.CharacterType.SUPPORTING].items()
            ),
        )

    # ------------------------------------------------------------------------------------------------------------------

    def _get_anime_characters_from_web(self, anime_id: AnimeId) -> Dict[enums.CharacterType, CharacterList]:
        with Cache("web,anime,characters", anime_id) as cache:
            try:
                raw_html_page = cache.get()
            except CacheDataNotFound:
                raw_html_page = self.get_request(
                    furl(f"https://myanimelist.net/anime/{anime_id}/_/characters"),
                    headers={"Referer": f"https://myanimelist.net/anime/{anime_id}"},
                )
                cache.set(raw_html_page)

        return MALWeb(anime_characters_page=raw_html_page).extract_anime_characters_from_html()

    def _get_anime_episode_from_web(self, anime_id: AnimeId, episode_no: EpisodeNumber) -> ApiResponseDataDict:
        with Cache("web,anime,episode", episode_id(anime_id, episode_no)) as cache:
            try:
                raw_html_page = cache.get()
            except CacheDataNotFound:
                raw_html_page = self.get_request(
                    furl(f"https://myanimelist.net/anime/{anime_id}/_/episode/{episode_no}"),
                    headers={"Referer": f"https://myanimelist.net/anime/{anime_id}/episode"},
                )
                cache.set(raw_html_page)

        return MALWeb(episode_page=raw_html_page).extract_episode_from_html()

    def _get_anime_episodes_from_web(self, anime_id: AnimeId) -> Sequence[RawEpisode]:
        with Cache("web,anime,episodes", anime_id) as cache:
            try:
                raw_html_page = cache.get()
            except CacheDataNotFound:
                raw_html_page = self.get_request(
                    furl(f"https://myanimelist.net/anime/{anime_id}/_/episode"),
                    headers={"Referer": f"https://myanimelist.net/anime/{anime_id}/episode"},
                )
                cache.set(raw_html_page)

        episodes = MALWeb(anime_episodes_page=raw_html_page).extract_episodes_from_html()
        for episode in episodes:
            episode_details = self._get_anime_episode_from_web(anime_id, episode["no"])
            episode["plot"] = episode_details["synopsis"]
        return episodes

    def _get_anime_from_api(self, anime_id: AnimeId) -> MALApiResponse:
        with Cache("apiv2,anime", anime_id) as cache:
            try:
                raw_stringified_json = cache.get()
            except CacheDataNotFound:
                # https://myanimelist.net/apiconfig/references/api/v2#operation/anime_anime_id_get
                url = furl(f"https://api.myanimelist.net/v2/anime/{anime_id}")
                url.set({"fields": ",".join(MAL_DATA)})
                raw_stringified_json = self.get_request(
                    url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                cache.set(raw_stringified_json)

        return json.loads(raw_stringified_json)

    def _get_anime_staff_from_web(self, anime_id: AnimeId) -> StaffList:
        with Cache("web,anime,characters", anime_id) as cache:
            try:
                raw_html_page = cache.get()
            except CacheDataNotFound:
                raw_html_page = self.get_request(
                    furl(f"https://myanimelist.net/anime/{anime_id}/_/characters"),
                    headers={"Referer": f"https://myanimelist.net/anime/{anime_id}"},
                )
                cache.set(raw_html_page)

        return MALWeb(anime_characters_page=raw_html_page).extract_anime_staff_from_html()

    def _get_character_from_web(self, anime_id: AnimeId) -> RawCharacter:
        with Cache("web,character", anime_id) as cache:
            try:
                raw_html_page = cache.get()
            except CacheDataNotFound:
                raw_html_page = self.get_request(
                    furl(f"https://myanimelist.net/character/{anime_id}"),
                    headers={"Referer": "https://myanimelist.net/"},
                )
                cache.set(raw_html_page)

        return MALWeb(character_page=raw_html_page).extract_character_from_html()


def _raw_data_to_dto(
    *,
    episodes_list: Sequence[RawEpisode],
    main_characters: OrderedDict[CharacterName, RawCharacter],
    mal_api_data: MALApiResponse,
    staff_list: StaffList,
    supporting_characters: OrderedDict[CharacterName, RawCharacter],
) -> dtos.TvSeriesData:
    api_data_parser = MALApi(mal_api_data)

    characters = []
    for name, data in list(main_characters.items()) + list(supporting_characters.items()):
        for seiyuu in data["seiyuu"].get(enums.Language.JAPANESE, []):
            characters.append(dtos.ShowCharacter(name=name, seiyuu=seiyuu))

    return dtos.TvSeriesData(
        provider=MALProvider,
        raw={"api": mal_api_data},
        # ID
        id=mal_api_data["id"],
        # CHARACTER
        characters=characters,
        # DATES
        dates=dtos.ShowDate(
            premiered=mal_api_data.get("start_date"),
            ended=mal_api_data.get("end_date"),
        ),
        # EPISODES
        episodes=raw_episodes_list_to_dtos(episodes_list, mal_api_data.get("num_episodes", 0), mal_api_data["id"]),
        # GENRES
        genres=api_data_parser.get_genres(),
        # IMAGES
        images=dtos.ShowImage(
            folder=api_data_parser.get_main_picture(),
        ),
        # MPAA
        mpaa=api_data_parser.get_mpaa(),
        # PLOT
        plot=api_data_parser.get_plot(),
        # RATING
        rating=mal_api_data.get("mean"),
        # SOURCE MATERIAL
        source_material=api_data_parser.get_source_material(),
        # STAFF
        staff=dtos.ShowStaff(
            director=utils.collect_staff(staff_list, "direction", "director"),
            music=utils.collect_staff(staff_list, "music"),
            screenwriter=utils.collect_staff(staff_list, "composition", "script"),
        ),
        # STUDIOS
        studios=api_data_parser.get_studios(),
        # TITLES
        titles=api_data_parser.get_titles(),
    )


class MALApi:
    def __init__(self, mal_api_data: MALApiResponse) -> None:
        self.mal_api_data = mal_api_data
        super().__init__()

    def get_genres(self) -> Set[str]:
        return set(str(item["name"]) for item in self.mal_api_data.get("genres", []))

    def get_main_picture(self) -> Optional[str]:
        _main_picture = self.mal_api_data.get("main_picture", {})
        return _main_picture.get("large", _main_picture.get("medium"))

    def get_mpaa(self) -> enums.MPAA:
        # fmt: off
        mal2mpaa = {
            "g":     enums.MPAA.G,      # All Ages                    # noqa: E241
            "pg":    enums.MPAA.PG,     # Children                    # noqa: E241
            "pg_13": enums.MPAA.PG_13,  # Teens 13 or older           # noqa: E241
            "r":     enums.MPAA.R,      # 17+ (violence & profanity)  # noqa: E241
            "r+":    enums.MPAA.NC_17,  # Mild Nudity                 # noqa: E241
            "rx":    enums.MPAA.X,      # Hentai                      # noqa: E241
        }
        # fmt: on
        return mal2mpaa.get(
            self.mal_api_data.get("rating", "").lower(),
            enums.MPAA.G,
        )

    def get_plot(self) -> str:
        return utils.normalize_string(self.mal_api_data.get("synopsis"))

    def get_source_material(self) -> enums.SourceMaterial:
        _source = self.mal_api_data.get("source", "other").lower()

        if "manga" in _source:
            return enums.SourceMaterial.MANGA

        if "game" in _source or "visual" in _source:
            return enums.SourceMaterial.GAME

        if "book" in _source or _source in ["novel", "light_novel"]:
            return enums.SourceMaterial.LIGHT_NOVEL

        if "original" in _source:
            return enums.SourceMaterial.ORIGINAL

        return enums.SourceMaterial.OTHER

    def get_studios(self) -> Set[str]:
        return set(str(item["name"]) for item in self.mal_api_data.get("studios", []))

    def get_titles(self) -> Dict[enums.Language, AnimeTitle]:
        result = {
            enums.Language.ROMAJI: self.mal_api_data["title"].strip(),
        }

        en = self.mal_api_data["alternative_titles"].get(enums.Language.ENGLISH.value.alpha2)
        if en:
            result[enums.Language.ENGLISH] = en  # type:ignore
        jp = self.mal_api_data["alternative_titles"].get(enums.Language.JAPANESE.value.alpha2)
        if jp:
            result[enums.Language.JAPANESE] = jp  # type:ignore

        return result


class MALWeb:
    def __init__(
        self,
        *,
        anime_characters_page: bytes = None,
        anime_episodes_page: bytes = None,
        character_page: bytes = None,
        episode_page: bytes = None,
    ) -> None:
        self.anime_characters_page = anime_characters_page
        self.anime_episodes_page = anime_episodes_page
        self.character_page = character_page
        self.episode_page = episode_page
        super().__init__()

    def extract_anime_characters_from_html(self) -> Dict[enums.CharacterType, CharacterList]:
        if not self.anime_characters_page:
            raise ValueError
        the_page = utils.load_html(self.anime_characters_page)

        main_characters = {}
        supporting_characters = {}

        for _h3 in the_page.xpath("//*[contains(@class, 'h3_character_name')]"):  # type:HtmlElement
            _td: HtmlElement = _h3.xpath("./ancestor::td[position()=1]")[0]
            _href: HtmlElement = _h3.xpath("./ancestor::a[position()=1]")[0]

            _name: str = _h3.text.split("(")[0].strip()
            _type: str = _td.xpath("./*[contains(@class, 'spaceit_pad')][position()=2]")[0].text.strip()
            _id: str = _href.attrib["href"].split("character/")[-1].split("/", 1)[0]

            if _type == "Main":
                main_characters[utils.reverse_name_order(_name)] = _id
            elif _type == "Supporting":
                supporting_characters[utils.reverse_name_order(_name)] = _id

        return {
            enums.CharacterType.MAIN: collections.OrderedDict(sorted(main_characters.items())),
            enums.CharacterType.SUPPORTING: collections.OrderedDict(sorted(supporting_characters.items())),
        }

    def extract_anime_staff_from_html(self) -> StaffList:
        if not self.anime_characters_page:
            raise ValueError
        the_page = utils.load_html(self.anime_characters_page)

        _staff_h2: HtmlElement = the_page.xpath("//h2[contains(text(), 'Staff')][contains(@class, 'h2_overwrite')]")[0]
        _staff: List[HtmlElement] = _staff_h2.xpath("./ancestor::div[position()=1]")[0].xpath(
            "./following-sibling::table"
        )

        result = collections.defaultdict(set)

        for item in _staff:
            for link in item.xpath(".//a[contains(@href, 'myanimelist.net/people/')]"):  # type: HtmlElement
                if not link.text_content().strip():
                    continue

                _position: str = link.xpath("./ancestor::td[position()=1]/div/small")[0].text.strip()
                positions: List[str] = list(map(str.strip, _position.split(",")))

                for position_name in positions:
                    result[position_name].add(utils.reverse_name_order(link.text.strip()))

        return result

    def extract_character_from_html(self) -> RawCharacter:
        if not self.character_page:
            raise ValueError
        the_page = utils.load_html(self.character_page)

        _content: HtmlElement = the_page.xpath("//*[@id='content']")[0]
        _name_en: HtmlElement = _content.xpath("//h2[contains(@class, 'normal_header')]")[0]
        _name_jp_jp: HtmlElement = _name_en.find("./span/small")
        _seiyuus: List[HtmlElement] = _content.xpath("//table//a[contains(@href, 'myanimelist.net/people/')]")

        result: RawCharacter = {
            "name": {
                enums.Language.ENGLISH: _name_en.text.split("(")[0].strip(),
            },
            "seiyuu": collections.defaultdict(set),
        }

        if getattr(_name_jp_jp, "text", ""):
            result["name"][enums.Language.JAPANESE] = _name_jp_jp.text.strip(" ()")

        for seiyuu in _seiyuus:
            if not seiyuu.text_content().strip():
                continue
            seiyuu_name: str = seiyuu.text.strip()
            seiyuu_lang = babelfish.Language.fromname(
                seiyuu.xpath("./ancestor::td[position()=1]/div/small")[0].text.strip()
            )
            result["seiyuu"][seiyuu_lang].add(utils.reverse_name_order(seiyuu_name))

        return result

    def extract_episode_from_html(self) -> Dict[str, str]:
        if not self.episode_page:
            raise ValueError
        the_page = utils.load_html(self.episode_page)

        return {
            "synopsis": utils.normalize_string(
                the_page.xpath("//h2[contains(text(), 'Synopsis')]/ancestor::*[position()=1]")[0].text_content()[8:]
            )
        }

    def extract_episodes_from_html(self) -> Sequence[RawEpisode]:  # noqa: C901
        if not self.anime_episodes_page:
            raise ValueError
        the_page = utils.load_html(self.anime_episodes_page)

        result = []

        _table: HtmlElement = the_page.xpath("//table[contains(@class, 'episode_list')][contains(@class, 'ascend')]")[0]
        for episode in _table.xpath("./tr[contains(@class, 'episode-list-data')]"):  # type: HtmlElement
            ep: RawEpisode = {
                "no": int(episode.xpath("./td[contains(@class, 'episode-number')]")[0].text.strip()),
                "titles": {
                    enums.Language.ENGLISH: episode.xpath("./td[contains(@class, 'episode-title')]/a")[0].text.strip(),
                },
                "premiered": episode.xpath("./td[contains(@class, 'episode-aired')]")[0].text.strip(),
            }
            try:
                jp_titles = episode.xpath("./td[contains(@class, 'episode-title')]/span")[0].text.strip().split("(")
                if jp_titles:
                    ep["titles"][enums.Language.ROMAJI] = jp_titles[0].replace("\xa0", "").strip(" ()")
                if len(jp_titles) == 2:
                    ep["titles"][enums.Language.JAPANESE] = jp_titles[0].replace("\xa0", "").strip(" ()")
            except AttributeError:
                pass
            result.append(ep)

        return result


def raw_episodes_list_to_dtos(  # noqa: C901
    episodes_list: Sequence[RawEpisode],
    total_episodes: int,
    anime_id: AnimeId,
) -> Sequence[dtos.ShowEpisode]:
    if total_episodes == 0 or not episodes_list:
        return []
    if len(episodes_list) != total_episodes:
        raise NotImplementedError

    _episodes = {item["no"]: item for item in episodes_list}
    result = []

    for i in range(1, total_episodes + 1):
        if i not in _episodes:
            continue

        result.append(
            dtos.ShowEpisode(
                no=i,
                id=episode_id(anime_id, i),
                plot=_episodes[i].get("plot", ""),
                premiered=_episodes[i]["premiered"],
                rating=None,
                titles=_episodes[i]["titles"],
            )
        )

    if len(result) != total_episodes:
        raise NotImplementedError

    return result


def episode_id(anime_id: AnimeId, episode_no: EpisodeNumber) -> str:
    return f"{anime_id}/{episode_no}"
