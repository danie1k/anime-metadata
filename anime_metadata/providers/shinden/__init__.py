import datetime
from typing import Any, Dict, Iterator, List, Optional, Union, cast

from bs4 import BeautifulSoup
from furl import furl
from lxml import html
from lxml.html import HtmlElement

from anime_metadata import constants, dtos, enums, interfaces, utils
from anime_metadata.exceptions import CacheDataNotFound, ProviderResultFound
from anime_metadata.typeshed import AnimeId, AnimeTitle

from .typeshed import SearchResult

__all__ = [
    "ShindenProvider",
]

MAX_SEARCH_PAGES = 5


class Cache(interfaces.BaseCache):
    provider_name = "shinden"


class ShindenProvider(interfaces.BaseProvider):
    def _find_series_by_title(self, title: AnimeTitle, year: Optional[int]) -> dtos.TvSeriesData:
        try:
            utils.find_title_in_provider_results(
                title=title,
                data=self._search_shinden_with_pagination(title, year),  # type:ignore
                data_item_title_getter=lambda item: cast(SearchResult, item)["title"],
                title_similarity_factor=self.title_similarity_factor,
            )
        except ProviderResultFound as exc:
            data_item: SearchResult = exc.data_item  # type:ignore
            return self._get_series_by_id(data_item["id"])

        raise NotImplementedError

    def _get_series_by_id(self, anime_id: AnimeId) -> dtos.TvSeriesData:
        with Cache("web,series", anime_id) as cache:
            try:
                raw_html_page = cache.get()
            except CacheDataNotFound:
                raw_html_page = self.get_request(
                    furl(f"https://shinden.pl/series/{anime_id}"),
                    headers={
                        "User-Agent": constants.USER_AGENT,
                        "Referer": "https://shinden.pl",
                    },
                )
                cache.set(raw_html_page)

        return ShindenWeb(anime_id, series_page=raw_html_page).extract_series_data()

    # ------------------------------------------------------------------------------------------------------------------

    def _search_shinden_with_pagination(self, title: AnimeTitle, year: int = None) -> Iterator[SearchResult]:
        url = furl("https://shinden.pl/series")
        url.set({"search": title, "type": "contains", "sort_by": "score", "sort_order": "asc"})

        if year:
            url.add({"start_date_precision": 1, "year_from": year})

        referer = "https://shinden.pl"

        for _unused in range(MAX_SEARCH_PAGES):
            response = self.get_request(
                url,
                headers={"User-Agent": constants.USER_AGENT, "Referer": referer},
            )
            data = ShindenWeb(search_result_page=response).extract_search_results()

            if not data["items"]:
                break

            for item in data["items"]:
                yield cast(SearchResult, item)

            if data["_next_page"] is None:
                break
            else:
                referer = url.tostr()
                url = data["_next_page"]


class ShindenWeb:
    def __init__(
        self, anime_id: AnimeId = None, *, series_page: bytes = None, search_result_page: bytes = None
    ) -> None:
        self.anime_id = anime_id
        self.series_page = series_page
        self.search_result_page = search_result_page
        super().__init__()

    def extract_series_data(self) -> dtos.TvSeriesData:
        if not self.series_page:
            raise ValueError
        the_page = utils.load_html(self.series_page)

        basic_information = self._extract_show_basic_information(the_page)
        tags = self._extract_show_tags(the_page)

        return dtos.TvSeriesData(
            provider=ShindenProvider,
            raw={"web": self.series_page},
            # TODO: characters=(),
            # DATES
            dates=basic_information["dates"],
            # TODO: episodes=(),
            # GENRES
            genres=tags["genres"],
            # ID
            id=self.anime_id,
            # IMAGES
            images=dtos.ShowImage(
                base_url="https://shinden.pl",
                folder=the_page.xpath("//*[normalize-space(@class)='title-cover']/a[contains(@href, '/images/')]")[
                    0
                ].attrib["href"],
            ),
            # MPAA
            mpaa=basic_information["mpaa"],
            # PLOT
            plot=utils.normalize_string(self._extract_show_plot(the_page)),
            # RATING
            rating=self._extract_show_rating(the_page),
            # SOURCE_MATERIAL
            source_material=tags["source_material"],
            # TODO: staff=(),
            # TODO: studios=(),
            titles={
                enums.Language.ENGLISH: self._extract_show_title(the_page),
            },
        )

    def _extract_show_title(self, the_page: HtmlElement) -> AnimeTitle:
        return the_page.xpath("//h1[contains(@class, 'page-title')]//*[normalize-space(@class)='title']")[
            0
        ].text.strip()

    def _extract_show_plot(self, the_page: HtmlElement) -> str:
        raw_description: HtmlElement = the_page.xpath("//*[normalize-space(@id)='description']")[0]
        return html.tostring(raw_description)

    def _extract_show_rating(self, the_page: HtmlElement) -> Optional[str]:
        data: List[HtmlElement] = the_page.xpath("//*[normalize-space(@class)='info-aside-rating-user']")
        if not data:
            return None

        return data[0].text.strip().replace(",", ".")

    def _extract_show_tags(self, the_page: HtmlElement) -> Dict[str, Any]:  # noqa: C901
        tags_etc: List[HtmlElement] = the_page.xpath(
            "//*[normalize-space(@class)='info-top-table-highlight']//ul[normalize-space(@class)='tags']//a"
        )

        genres = set()
        source_material = None

        for a_ in tags_etc:
            href = a_.attrib["href"]
            text = a_.text.strip()

            if "/source/" in href:
                text = text.lower()
                # https://shinden.pl/source
                if "gra" in text or "gry" in text or "visual novel" in text:
                    source_material = enums.SourceMaterial.GAME
                elif "książka" in text or "light novel" in text or "novel" in text:
                    source_material = enums.SourceMaterial.LIGHT_NOVEL
                elif "manga" in text:
                    source_material = enums.SourceMaterial.MANGA
                elif "oryginalna" in text:
                    source_material = enums.SourceMaterial.ORIGINAL
                else:
                    source_material = enums.SourceMaterial.OTHER

            else:
                genres.add(text)

        return {
            "genres": genres,
            "source_material": source_material,
        }

    def _extract_show_basic_information(self, the_page: HtmlElement) -> Dict[str, Any]:
        basic_information: List[HtmlElement] = the_page.xpath(
            "//*[normalize-space(@class)='title-small-info']//dl[normalize-space(@class)='info-aside-list']/dt"
        )
        date_premiered = None
        date_ended = None
        mpaa = None

        for dt in basic_information:
            dd: HtmlElement = dt.xpath("./following-sibling::dd[1]")[0]
            title = dt.text
            descr = dd.text.strip() if dd.text else None

            if "Data emisji" in title:
                date_premiered = datetime.datetime.strptime(descr, "%d.%m.%Y").date()
            elif "Koniec emisji" in title:
                date_ended = datetime.datetime.strptime(descr, "%d.%m.%Y").date()

            elif "MPAA" in title:
                mpaa = enums.MPAA(descr)

        return {
            "dates": dtos.ShowDate(premiered=date_premiered, ended=date_ended),
            "mpaa": mpaa,
        }

    def extract_search_results(self) -> Dict[str, Union[None, str, List[SearchResult]]]:  # noqa: C901
        if not self.search_result_page:
            raise ValueError
        the_page = utils.load_html(self.search_result_page)

        result = []
        for item in the_page.xpath("//*[normalize-space(@class)='title-table']//ul[normalize-space(@class)='div-row']"):
            try:
                image: str = item.xpath(".//li[normalize-space(@class)='cover-col']/a")[0].attrib["href"]
            except IndexError:
                continue

            result.append(
                {
                    "image": image,
                    "title": BeautifulSoup(
                        html.tostring(item.xpath(".//li[normalize-space(@class)='desc-col']//a")[0]), features="lxml"
                    ).get_text(" "),
                    "id": (
                        item.xpath(".//li[normalize-space(@class)='desc-col']//a")[0]
                        .attrib["href"]
                        .rsplit("/", 1)[-1]
                        .split("-", 1)[0]
                    ),
                    "type": item.xpath(".//li[normalize-space(@class)='title-kind-col']")[0].text.strip(),
                    "total_episodes": int(item.xpath(".//li[normalize-space(@class)='episodes-col']")[0].text.strip()),
                    "status": item.xpath(".//li[normalize-space(@class)='title-status-col']")[0].text.strip(),
                    "rating": item.xpath(".//li[normalize-space(@class)='rate-top']")[0].text.strip().replace(",", "."),
                }
            )

        _prev_page = None
        _next_page = None
        try:
            _prev_page = furl(
                "https://shinden.pl"
                + the_page.xpath("//*[normalize-space(@class)='pagination-prev']//a")[0].attrib["href"]
            )
            _prev_page.remove(args=["r307"])
        except IndexError:
            pass
        try:
            _next_page = furl(
                "https://shinden.pl"
                + the_page.xpath("//*[normalize-space(@class)='pagination-next']//a")[0].attrib["href"]
            )
            _next_page.remove(args=["r307"])
        except IndexError:
            pass

        return {"items": result, "_prev_page": _prev_page, "_next_page": _next_page}
