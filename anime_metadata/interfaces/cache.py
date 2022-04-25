from contextlib import AbstractContextManager, ContextDecorator
from typing import Optional

from anime_metadata import models
from anime_metadata.exceptions import CacheDataNotFound
from anime_metadata.typeshed import RawHtml

__all__ = (
    "BaseCache",
)


class BaseCache(ContextDecorator, AbstractContextManager):
    @property
    def provider_name(self) -> str:
        raise NotImplementedError

    def __init__(self, data_type: str, _id: str) -> None:
        self.id = _id
        self.data_type = data_type
        super().__init__()

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_value:
            raise exc_value

    def get(self) -> Optional[RawHtml]:
        result = models.ProviderCache.get(self.provider_name, self.id, self.data_type)
        if result is None:
            raise CacheDataNotFound
        return result

    def set(self, value: RawHtml) -> None:
        return models.ProviderCache.set(self.provider_name, self.id, self.data_type, value)
