from contextlib import AbstractContextManager, ContextDecorator
from types import TracebackType
from typing import Optional, Type, Union

from anime_metadata import models
from anime_metadata.exceptions import CacheDataNotFound
from anime_metadata.typeshed import RawHtml

__all__ = [
    "BaseCache",
]


class BaseCache(AbstractContextManager, ContextDecorator):  # type:ignore
    @property
    def provider_name(self) -> str:
        raise NotImplementedError

    def __init__(self, data_type: str, _id: Union[str, int]) -> None:
        self.id = _id
        self.data_type = data_type
        super().__init__()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        if exc_value:
            raise exc_value
        return None

    def get(self) -> Optional[RawHtml]:
        result = models.ProviderCache.get(self.provider_name, self.id, self.data_type)  # type:ignore
        if result is None:
            raise CacheDataNotFound
        return result

    def set(self, value: RawHtml) -> None:
        models.ProviderCache.set(self.provider_name, self.id, self.data_type, value)  # type:ignore
        return None
