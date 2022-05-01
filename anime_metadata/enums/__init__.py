import enum

from .language import *  # noqa


class CharacterType(enum.Enum):
    MAIN = enum.auto()
    SUPPORTING = enum.auto()


class EpisodeType(enum.Enum):
    REGULAR = enum.auto()
    SPECIAL = enum.auto()
    OVA = enum.auto()


class MPAA(enum.Enum):
    AO = "AO"
    APPROVED = "APPROVED"
    E = "E"
    EC = "EC"
    G = "G"
    M = "M"
    NC_17 = "NC-17"
    NR = "NR"
    PG = "PG"
    PG_13 = "PG-13"
    R = "R"
    RP = "RP"
    T = "T"
    TV_14 = "TV-14"
    TV_G = "TV-G"
    TV_MA = "TV-MA"
    TV_PG = "TV-PG"
    TV_Y = "TV-Y"
    TV_Y7 = "TV-Y7"
    TV_Y7_FV = "TV-Y7-FV"
    UR = "UR"
    X = "X"
    XXX = "XXX"


class SourceMaterial(enum.Enum):
    GAME = enum.auto()
    LIGHT_NOVEL = enum.auto()
    MANGA = enum.auto()
    ORIGINAL = enum.auto()
    OTHER = enum.auto()
