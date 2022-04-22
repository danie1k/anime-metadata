
class AnimeMetadataError(Exception):
    pass


class AnimeMetadataProviderError(AnimeMetadataError):
    pass


class ProviderNoResultError(AnimeMetadataProviderError):
    pass


class ProviderMultipleResultError(AnimeMetadataProviderError):
    pass


class ValidationError(AnimeMetadataError):
    pass

