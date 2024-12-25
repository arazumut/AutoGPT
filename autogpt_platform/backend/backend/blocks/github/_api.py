from urllib.parse import urlparse

from backend.blocks.github._auth import GithubKimlikBilgileri
from backend.util.request import Istekler


def _api_url_çevir(url: str) -> str:
    """
    Standart bir GitHub URL'sini ilgili GitHub API URL'sine dönüştürür.
    Depo URL'leri, sorun URL'leri, çekme isteği URL'leri ve daha fazlasını işler.
    """
    çözümlenmiş_url = urlparse(url)
    yol_parçaları = çözümlenmiş_url.path.strip("/").split("/")

    if len(yol_parçaları) >= 2:
        sahip, depo = yol_parçaları[0], yol_parçaları[1]
        api_taban = f"https://api.github.com/repos/{sahip}/{depo}"

        if len(yol_parçaları) > 2:
            ek_yol = "/".join(yol_parçaları[2:])
            api_url = f"{api_taban}/{ek_yol}"
        else:
            # Depo taban URL'si
            api_url = api_taban
    else:
        raise ValueError("Geçersiz GitHub URL formatı.")

    return api_url


def _başlıklar_al(kimlik_bilgileri: GithubKimlikBilgileri) -> dict[str, str]:
    return {
        "Authorization": kimlik_bilgileri.bearer(),
        "Accept": "application/vnd.github.v3+json",
    }


def api_al(kimlik_bilgileri: GithubKimlikBilgileri, url_çevir: bool = True) -> Istekler:
    return Istekler(
        güvenilir_kökenler=["https://api.github.com", "https://github.com"],
        ekstra_url_doğrulayıcı=_api_url_çevir if url_çevir else None,
        ekstra_başlıklar=_başlıklar_al(kimlik_bilgileri),
    )
