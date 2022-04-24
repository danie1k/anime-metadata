from datetime import datetime
from typing import Union

import peewee

from anime_metadata import constants
from .base import BaseModel

__all__ = (
    "ProviderCache",
)


class ProviderCache(BaseModel):
    id: str = peewee.CharField(max_length=10, index=True)
    provider: str = peewee.CharField(max_length=20, index=True)
    data_type: str = peewee.CharField(max_length=20, index=True)
    last_update: datetime = peewee.DateTimeField(default=datetime.utcnow)
    data: memoryview = peewee.BlobField()

    class Meta:
        table_name = "providers_cache"
        primary_key = peewee.CompositeKey('id', 'provider', 'data_type')

    @classmethod
    def get(cls, provider: str, _id: str, _type: str) -> Union[bytes, None]:
        try:
            result: "ProviderCache" = super().get(
                cls.provider == provider,
                cls.id == _id,
                cls.data_type == _type,
            )
        except peewee.DoesNotExist:
            return None

        if result.last_update + constants.MAX_CACHE_LIFETIME <= datetime.utcnow():
            return None

        return result.data.tobytes()

    @classmethod
    def set(cls, provider: str, _id: str, _type: str, data: bytes) -> None:
        item, _created = cls.get_or_create(
            id=_id,
            provider=provider,
            data_type=_type,
            defaults={
                "data": data,
            },
        )
        item.data = data
        item.save()
