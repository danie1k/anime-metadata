from anime_metadata.typeshed import ApiResponseData


class AnimeMetadataError(Exception):
    pass


class AnimeMetadataProviderError(AnimeMetadataError):
    pass


class ProviderResultFound(StopIteration):
    def __init__(self, data_item: ApiResponseData, *args: object) -> None:
        self.data_item = data_item
        super().__init__(*args)


class ProviderNoResultError(AnimeMetadataProviderError):
    pass


class ProviderMultipleResultError(AnimeMetadataProviderError):
    pass


class ValidationError(AnimeMetadataError):
    pass


class CacheDataNotFound(AnimeMetadataError):
    pass
