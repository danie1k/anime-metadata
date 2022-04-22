import json
from typing import Dict, Any, List, Optional

import requests
from furl import furl
from rapidfuzz.distance import Indel

import anime_metadata.dtos.show
from anime_metadata import interfaces, models, dtos
from anime_metadata.exceptions import ProviderNoResultError, ProviderMultipleResultError

__all__ = (
    "TMDBProvider",
)


class TMDBProvider(interfaces.BaseProvider):
    _cache_provider_ = "tmdb"

    def __init__(self, api_key: str, lang: str = "en-US", title_similarity_factor: float = 0.9) -> None:
        self.api_key = api_key
        self.lang = lang
        self.title_similarity_factor = title_similarity_factor
        super().__init__()

    def _get_series_by_id(self, _id: str) -> dtos.ProviderSeriesData:
        json_data: Dict[str, Any]

        _cache_data_type_ = "apiv3,tv"
        _cache = models.ProviderCache.get(self._cache_provider_, _id, _cache_data_type_)
        if _cache:
            return _json_data_to_dto(json.loads(_cache.decode("utf-8")))

        # https://developers.themoviedb.org/3/tv/get-tv-details
        url = furl("https://api.themoviedb.org/3/tv")
        url.path.add(_id)
        url.set({
            "api_key": self.api_key,
            "language": self.lang,
        })
        response = requests.get(url.tostr())
        response.raise_for_status()

        models.ProviderCache.set(self._cache_provider_, _id, _cache_data_type_, response.content)

        _json_data_to_dto(response.json())

    def _search_series_by_title(self, title: str, year: Optional[int]) -> dtos.ProviderSeriesData:
        # https://developers.themoviedb.org/3/search/search-tv-shows
        url = furl("https://api.themoviedb.org/3/search/tv")
        url.set({
            "api_key": self.api_key,
            "include_adult": "true",
            "language": self.lang,
            "page": 1,
            "query": title,
        })

        if year:
            url.args["first_air_date_year"] = year

        response = requests.get(url.tostr())
        response.raise_for_status()

        json_data: Dict[str, Any] = response.json()
        json_results: List[Dict[str, Any]] = json_data.get("results", [])

        if len(json_results) == 0:
            raise ProviderNoResultError

        if len(json_results) == 1:
            return _json_data_to_dto(json_results[0])

        results = []

        for item in json_results:
            cmp = Indel.normalized_similarity(item["name"], title)
            if cmp == 1.0:
                return _json_data_to_dto(item)

            if cmp >= self.title_similarity_factor:
                results.append(item)

        # TODO: Handle multiple results
        raise ProviderMultipleResultError


def _json_data_to_dto(json_data: Dict[str, Any]) -> dtos.ProviderSeriesData:
    if json_data.get("created_by"):
        raise NotImplementedError("created_by")

    return dtos.ProviderSeriesData(
        id=str(json_data["id"]),
        images=anime_metadata.dtos.show.ShowImage(
            base_url="https://www.themoviedb.org/t/p/original",
            backdrop=json_data.get("backdrop_path"),
            folder=json_data.get("poster_path"),
        ),
        titles=anime_metadata.dtos.show.ShowTitle(
            en=json_data.get("name"),
            jp_jp=json_data.get("original_name"),
        ),
        dates=anime_metadata.dtos.show.ShowDate(
            premiered=json_data.get("first_air_date"),
            ended=json_data.get("last_air_date"),
        ),
        plot=json_data.get("overview", ""),
        rating=json_data.get("vote_average"),
        staff=anime_metadata.dtos.show.ShowStaff(
            # TODO
        ),
    )
