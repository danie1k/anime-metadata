import json
from typing import Any, Optional, cast

from furl import furl

from anime_metadata import dtos, enums, interfaces, utils
from anime_metadata.exceptions import CacheDataNotFound, ProviderResultFound
from anime_metadata.typeshed import AnimeTitle, ApiResponseDataDict, TvShowId

__all__ = [
    "TMDBProvider",
]


class Cache(interfaces.BaseCache):
    provider_name = "tmdb"


class TMDBProvider(interfaces.BaseProvider):
    def __init__(self, lang: str = "en-US", *args: Any, **kwargs: Any) -> None:
        self.lang = lang
        super().__init__(*args, **kwargs)

    def _find_series_by_title(self, title: AnimeTitle, year: Optional[int]) -> dtos.TvSeriesData:
        # https://developers.themoviedb.org/3/search/search-tv-shows
        url = furl("https://api.themoviedb.org/3/search/tv")
        url.set(
            {
                "api_key": self.api_key,
                "include_adult": "true",
                "language": self.lang,
                "page": 1,
                "query": title,
            }
        )

        if year:
            url.args["first_air_date_year"] = year

        response = self.get_request(url)
        json_data: ApiResponseDataDict = json.loads(response)

        try:
            utils.find_title_in_provider_results(
                title=title,
                data=json_data.get("results", []),
                data_item_title_getter=lambda item: cast(ApiResponseDataDict, item)["name"],
                title_similarity_factor=self.title_similarity_factor,
            )
        except ProviderResultFound as exc:
            data_item: ApiResponseDataDict = exc.data_item  # type:ignore
            return self._get_series_by_id(data_item["id"])

        raise NotImplementedError

    def _get_series_by_id(self, show_id: TvShowId) -> dtos.TvSeriesData:
        with Cache("apiv3,tv", show_id) as cache:
            try:
                raw_stringified_json = cache.get()
            except CacheDataNotFound:
                # https://developers.themoviedb.org/3/tv/get-tv-details
                url = furl("https://api.themoviedb.org/3/tv")
                url.path.add(show_id)
                url.set(
                    {
                        "api_key": self.api_key,
                        "language": self.lang,
                    }
                )
                raw_stringified_json = self.get_request(url)
                cache.set(raw_stringified_json)

        return _json_data_to_dto(json.loads(raw_stringified_json))


def _json_data_to_dto(json_data: ApiResponseDataDict) -> dtos.TvSeriesData:
    if json_data.get("created_by"):
        raise NotImplementedError("created_by")

    return dtos.TvSeriesData(
        raw={"api": json_data},
        # ID
        id=json_data["id"],
        # DATES
        dates=dtos.ShowDate(
            premiered=json_data.get("first_air_date"),
            ended=json_data.get("last_air_date"),
        ),
        # GENRES
        genres=set(item["name"] for item in json_data.get("genres", [])),
        # IMAGES
        images=dtos.ShowImage(
            base_url="https://www.themoviedb.org/t/p/original",
            backdrop=json_data.get("backdrop_path"),
            folder=json_data.get("poster_path"),
        ),
        # PLOT
        plot=json_data.get("overview"),
        # RATING
        rating=json_data.get("vote_average"),
        # STUDIOS
        studios=set(
            [
                *(item["name"] for item in json_data.get("networks", [])),
                *(item["name"] for item in json_data.get("production_companies", [])),
            ]
        ),
        # TITLES
        titles={
            enums.Language.ENGLISH: json_data.get("name"),
            enums.Language.JAPANESE: json_data.get("original_name"),
        },
    )
