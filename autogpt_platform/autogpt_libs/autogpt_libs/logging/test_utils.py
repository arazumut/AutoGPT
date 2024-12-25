import pytest

from .utils import renk_kodlarini_kaldir


@pytest.mark.parametrize(
    "ham_metin, temiz_metin",
    [
        (
            "KOMUT = \x1b[36mwebsitesini_gezin\x1b[0m  "
            "ARGÜMANLAR = \x1b[36m{'url': 'https://www.google.com',"
            " 'soru': 'Fransa'nın başkenti nedir?'}\x1b[0m",
            "KOMUT = websitesini_gezin  "
            "ARGÜMANLAR = {'url': 'https://www.google.com',"
            " 'soru': 'Fransa'nın başkenti nedir?'}",
        ),
        (
            "{'Projelerimi github'da () ve web sitelerimde inceleyin': "
            "'https://github.com/Significant-Gravitas/AutoGPT,"
            " https://discord.gg/autogpt ve https://twitter.com/Auto_GPT'}",
            "{'Projelerimi github'da () ve web sitelerimde inceleyin': "
            "'https://github.com/Significant-Gravitas/AutoGPT,"
            " https://discord.gg/autogpt ve https://twitter.com/Auto_GPT'}",
        ),
        ("", ""),
        ("merhaba", "merhaba"),
        ("merhaba\x1b[31m dünya", "merhaba dünya"),
        ("\x1b[36mMerhaba,\x1b[32m Dünya!", "Merhaba, Dünya!"),
        (
            "\x1b[1m\x1b[31mHata:\x1b[0m\x1b[31m dosya bulunamadı",
            "Hata: dosya bulunamadı",
        ),
    ],
)
def test_renk_kodlarini_kaldir(ham_metin, temiz_metin):
    assert renk_kodlarini_kaldir(ham_metin) == temiz_metin
