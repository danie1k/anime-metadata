import json
from typing import Any, List, Optional, Sequence, Union, cast

from furl import furl

from anime_metadata import constants, dtos, enums, interfaces, utils
from anime_metadata.exceptions import CacheDataNotFound, ProviderResultFound
from anime_metadata.typeshed import AnimeId, AnimeTitle

from .typeshed import ImageData, SearchResultItem, TvData

__all__ = [
    "FanartProvider",
]


class Cache(interfaces.BaseCache):
    provider_name = "fanart"


class FanartProvider(interfaces.BaseProvider):
    def __init__(self, preferred_lang: Sequence[enums.Language] = None, *args: Any, **kwargs: Any) -> None:
        preferred_lang = preferred_lang or [enums.Language.ENGLISH, enums.Language.JAPANESE, enums.Language.UNKNOWN]
        self.preferred_lang = [item.value for item in preferred_lang]
        super().__init__(*args, **kwargs)

    def _find_series_by_title(self, title: AnimeTitle, year: Optional[int]) -> dtos.TvSeriesData:
        url = furl("https://fanart.tv/api/search.php")
        url.set(
            {
                "section": "tv",
                "s": title,
            }
        )

        response = self.get_request(
            url,
            headers={
                "User-Agent": constants.USER_AGENT,
                "Referer": "https://fanart.tv",
                "X-Requested-With": "XMLHttpRequest",
                "Alt-Used": "fanart.tv",
            },
        )
        json_data: List[SearchResultItem] = json.loads(response)

        try:
            utils.find_title_in_provider_results(
                title=title,
                data=(item for item in json_data if int(item["image_count"]) > 0),  # type:ignore
                data_item_title_getter=lambda item: cast(SearchResultItem, item)["title"],
                title_similarity_factor=self.title_similarity_factor,
            )
        except ProviderResultFound as exc:
            return self._get_series_by_id(cast(SearchResultItem, exc.data_item)["id"])

        raise NotImplementedError

    def _get_series_by_id(self, anime_id: AnimeId) -> dtos.TvSeriesData:
        with Cache("api,tv", anime_id) as cache:
            try:
                raw_stringified_json = cache.get()
            except CacheDataNotFound:
                # https://fanarttv.docs.apiary.io/#reference/tv/get-show/get-images-for-show
                url = furl(f"http://webservice.fanart.tv/v3/tv/{anime_id}")
                url.set({"api_key": self.api_key})
                raw_stringified_json = self.get_request(url)
                cache.set(raw_stringified_json)

        json_data: TvData = json.loads(raw_stringified_json)

        return dtos.TvSeriesData(
            raw=json_data,
            genres=None,
            id=anime_id,
            images=dtos.ShowImage(
                backdrop=self._get_best_image(json_data["showbackground"]),
                banner=self._get_best_image(json_data["tvbanner"]),
                folder=self._get_best_image(json_data["tvposter"]),
                landscape=self._get_best_image(json_data["tvthumb"]),
                logo=self._get_best_image(json_data["hdtvlogo"]),
            ),
            titles={enums.Language.ENGLISH: json_data["name"]},
        )

    # ------------------------------------------------------------------------------------------------------------------

    def _get_best_image(self, data: List[ImageData]) -> Union[str, None]:
        lang_points = {lang: weight for weight, lang in enumerate(self.preferred_lang)}

        only_preferred_lang = filter(
            lambda item: item["lang"] in self.preferred_lang,
            data,
        )
        if not only_preferred_lang:
            return None

        sorted_images = sorted(
            only_preferred_lang,
            key=lambda item: (lang_points.get(item["lang"], 99), item["likes"], int(item["id"])),
        )
        return sorted_images[0]["url"]
