import pytest
from slugify import slugify


@pytest.mark.parametrize(
    "name,slug",
    [
        ("Bookshelf", "bookshelf"),
        ("Fanart", "fanart"),
        ("IMVDb", "imvdb"),
        ("Kodi Sync Queue", "kodi-sync-queue"),
        ("LDAP Authentication", "ldap-authentication"),
        ("NextPVR", "nextpvr"),
        ("Open Subtitles", "open-subtitles"),
        ("Playback Reporting", "playback-reporting"),
        ("Reports", "reports"),
        ("TMDb Box Sets", "tmdb-box-sets"),
        ("Trakt", "trakt"),
        ("TVHeadend", "tvheadend"),
        ("Cover Art Archive", "cover-art-archive"),
        ("TheTVDB", "thetvdb"),
        ("AniDB", "anidb"),
        ("AniList", "anilist"),
        ("AniSearch", "anisearch"),
        ("Kitsu", "kitsu"),
        ("TVMaze", "tvmaze"),
        ("Webhook", "webhook"),
        ("OPDS", "opds"),
        ("Session Cleaner", "session-cleaner"),
        ("VGMdb", "vgmdb"),
        ("Simkl", "simkl"),
        ("Subtitle Extract", "subtitle-extract"),
    ],
)
def test_slugify(name: str, slug: str):
    assert slugify(name) == slug
