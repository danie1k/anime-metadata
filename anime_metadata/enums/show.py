import enum

__all__ = (
    "ShowEpisodeType",
)


class ShowEpisodeType(enum.Enum):
    REGULAR = enum.auto()
    SPECIAL = enum.auto()
    OVA = enum.auto()
