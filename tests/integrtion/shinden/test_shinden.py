from datetime import datetime
from decimal import Decimal

from anime_metadata import dtos, enums
from anime_metadata.providers import ShindenProvider
from anime_metadata.typeshed import AnimeTitle


def test_search_series(shinden_base_web_url: str, shinden_provider: ShindenProvider) -> None:
    # GIVEN
    anime_title: AnimeTitle = "Bokutachi wa Benkyou ga Dekinai"

    # WHEN
    result = shinden_provider.search_series(anime_title)

    # THEN
    assert result.dates == dtos.ShowDate(premiered=datetime(2019, 4, 7).date(), ended=datetime(2019, 6, 30).date())
    assert result.episodes == None
    assert result.genres == {
        "Anime",
        "Dere-Dere",
        "Harem",
        "Japonia",
        "Komedia",
        "Loli",
        "Nauczyciele",
        "Pokojówki",
        "Romans",
        "Shounen",
        "Szkolne",
        "Uczniowie",
        "Współczesność",
    }
    assert result.id == '53932'
    assert result.images == dtos.ShowImage(base_url=shinden_base_web_url, folder="/res/images/genuine/242394.jpg")
    assert result.images.folder == f"{shinden_base_web_url}/res/images/genuine/242394.jpg"
    assert result.main_characters == None
    assert result.mpaa == enums.MPAA.PG_13
    assert result.plot == (
        "Nariyuki Yuiga za sprawą słów swojego zmarłego już ojca mówiącymi, że bezużyteczny człowiek powinien starać "
        "się być użyteczny, postanowił stać się osiągającym wysokie wyniki uczniem pomimo swoich wcześniejszych "
        "kiepskich ocen. Chcąc zapewnić swojej biednej rodzinie lepsze życie, obrał sobie za cel zdobycie specjalnej "
        "nominacji VIP, czyli prestiżowego stypendium pokrywającego wszystkie przyszłe czesne za studia.\n"
        "Ku swojemu szczęściu Nariyuki zdobył nominacje, ale niestety jest haczyk: musi uczyć dwie sławne koleżanki ze "
        "swojej szkoły, którymi są Fumino Furuhashi, geniusz w dziedzinie literatury, oraz Rizu Ogata, geniusz w "
        "dziedzinie nauk ścisłych. Sytuacje pogarsza to, że obie chcą rozwijać się w dziedzinach, w których są "
        "beznadziejnie słabe!"
    )
    assert result.rating == Decimal("7.78")
    assert result.secondary_characters == None
    assert result.source_material == enums.SourceMaterial.MANGA
    assert result.staff == None
    assert result.studios == {
        "Aniplex of America",
        "Aniplex",
        "Arvo Animation",
        "Barnum Studio",
        "Magic Capsule",
        "Movic",
        "Nippon BS Broadcasting Corporation",
        "Shueisha",
        "Silver",
    }
    assert result.titles == {
        enums.Language.ROMAJI: "Bokutachi wa Benkyou ga Dekinai",
    }

