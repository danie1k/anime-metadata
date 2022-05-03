from datetime import datetime
from decimal import Decimal

from anime_metadata import dtos, enums
from anime_metadata.providers import AniDBProvider
from anime_metadata.typeshed import AnimeTitle


def test_search_series(anidb_base_img_cdn_url: str, anidb_provider: AniDBProvider) -> None:
    # GIVEN
    anime_title: AnimeTitle = "Bokutachi wa Benkyou ga Dekinai"

    # WHEN
    result = anidb_provider.search_series(anime_title)

    # THEN
    assert result.dates == dtos.ShowDate(premiered=datetime(2019, 4, 7).date(), ended=datetime(2019, 6, 30).date())
    assert len(result.episodes) == 3
    assert result.episodes[0] == dtos.ShowEpisode(
        no=1,
        id="213397",
        type=enums.EpisodeType.REGULAR,
        premiered=datetime(2019, 4, 7).date(),
        rating=Decimal("5.59"),
        titles={
            enums.Language.ENGLISH: "Genius and X Are Two Sides of the Same Coin",
            enums.Language.JAPANESE: "天才と[X]は表裏一体である",
            enums.Language.ROMAJI: "Tensai to [X] wa Hyouriittai de Aru",
        },
        plot=(
            "There are two geniuses at Ichinose Academy: Fumino Furuhashi, a liberal arts prodigy, and Rizu Ogata..."
        )
    )
    assert result.episodes[1] == dtos.ShowEpisode(
        no=2,
        id="213398",
        type=enums.EpisodeType.REGULAR,
        premiered=datetime(2019, 4, 14).date(),
        rating=Decimal("5.99"),
        titles={
            enums.Language.ENGLISH: "A Fish Is to Water as a Genius Is to X",
            enums.Language.JAPANESE: "魚心あれば, 天才に[X]心あり",
            enums.Language.ROMAJI: "Uogokoro Areba, Tensai ni [X] Kokoro Ari",
        },
        plot=(
            "Uruka Takemoto has been a friend of Nariyuki's since middle school and is a swimming prodigy who should..."
        )
    )
    assert result.episodes[2] == dtos.ShowEpisode(
        no=3,
        id="213399",
        type=enums.EpisodeType.REGULAR,
        premiered=datetime(2019, 4, 21).date(),
        rating=Decimal("6.27"),
        titles={
            enums.Language.ENGLISH: "A Genius Resonates Emotionally with X",
            enums.Language.JAPANESE: "天才は[X]にも心通ずるものと知る",
            enums.Language.ROMAJI: "Tensai wa [X] ni mo Kokoro Tsuuzuru Mono to Shiru",
        },
        plot=(
            "The results of Nariyuki's tutoring are about to be put to the test with the midterm exams..."
        )
    )
    assert result.genres == {
        "Anime",
        "Harem",
        "Shounen",
    }
    assert result.id == '14289'
    assert result.images == dtos.ShowImage(base_url=anidb_base_img_cdn_url, folder="231593.jpg")
    assert result.images.folder == f"{anidb_base_img_cdn_url}/231593.jpg"
    assert result.main_characters == {
        dtos.ShowCharacter(name="Furuhashi Fumino", seiyuu="Haruka Shiraishi"),
        dtos.ShowCharacter(name="Kirisu Mafuyu", seiyuu="Lynn"),
        dtos.ShowCharacter(name="Kominami Asumi", seiyuu="Madoka Asahina"),
        dtos.ShowCharacter(name="Ogata Rizu", seiyuu="Miyu Tomita"),
        dtos.ShowCharacter(name="Takemoto Uruka", seiyuu="Sayumi Suzushiro"),
        dtos.ShowCharacter(name="Yuiga Nariyuki", seiyuu="Ryouta Oosaka"),
    }
    assert result.mpaa == None
    assert result.plot == (
        "Yuiga Nariyuki tutors three genius of different subjects in highschool to get a scholarship. Furuhashi Fumino "
        "is a genius on literature but horrible in math, Ogata Rizu is a genius on mathematics and science but "
        "literature and arts are terrible subjects for her and Takemoto Uruka is a genius in the athletic field but "
        "really bad in all the others. Together, they study very hard and want to get better at their worst subjects "
        "while Fumino and Ogata wants to go to college and work on these subjects for life."
    )
    assert result.rating == Decimal("5.60")
    assert result.secondary_characters == {
        dtos.ShowCharacter(name="Sekijou Sawako", seiyuu="Saori Oonishi"),
    }
    assert result.source_material == enums.SourceMaterial.MANGA
    assert result.staff == dtos.ShowStaff(
        director={"Masakatsu Sasaki", "Yoshiaki Iwasaki"},
        guest_star=None,
        music={"Masato Nakayama"},
        screenwriter={"Gou Zappa"},
    )
    assert result.studios == {
        "Arvo Animation",
        "Silver",
    }
    assert result.titles == {
        enums.Language.ENGLISH: "We Never Learn: Bokuben",
        enums.Language.ROMAJI: "Bokutachi wa Benkyou ga Dekinai",
        enums.Language.JAPANESE: "ぼくたちは勉強ができない",
    }
