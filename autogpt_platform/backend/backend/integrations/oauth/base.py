import logging
import time
from abc import ABC, abstractmethod
from typing import ClassVar

from backend.data.model import OAuth2Credentials
from backend.integrations.providers import ProviderName

logger = logging.getLogger(__name__)


class TemelOAuthHandler(ABC):
    # Sağlayıcı adı ve varsayılan kapsamlar
    SAGLAYICI_ADI: ClassVar[ProviderName]
    VARSAYILAN_KAPSAMLAR: ClassVar[list[str]] = []

    @abstractmethod
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """OAuthHandler başlatıcı metodu"""
        pass

    @abstractmethod
    def giris_url_al(self, kapsamlar: list[str], durum: str) -> str:
        """Kullanıcının yönlendirilebileceği bir giriş URL'si oluşturur"""
        pass

    @abstractmethod
    def kodu_tokenlara_degistir(self, kod: str, kapsamlar: list[str]) -> OAuth2Credentials:
        """Girişten alınan yetkilendirme kodunu bir dizi token ile değiştirir"""
        pass

    @abstractmethod
    def _tokenlari_yenile(self, kimlik_bilgileri: OAuth2Credentials) -> OAuth2Credentials:
        """Token yenileme mekanizmasını uygular"""
        pass

    @abstractmethod
    def tokenlari_iptal_et(self, kimlik_bilgileri: OAuth2Credentials) -> bool:
        """Verilen tokeni sağlayıcıda iptal eder,
        sağlayıcı desteklemiyorsa False döner"""
        pass

    def tokenlari_yenile(self, kimlik_bilgileri: OAuth2Credentials) -> OAuth2Credentials:
        if kimlik_bilgileri.saglayici != self.SAGLAYICI_ADI:
            raise ValueError(
                f"{self.__class__.__name__} diğer sağlayıcı '{kimlik_bilgileri.saglayici}' için token yenileyemez"
            )
        return self._tokenlari_yenile(kimlik_bilgileri)

    def erisim_tokeni_al(self, kimlik_bilgileri: OAuth2Credentials) -> str:
        """Geçerli bir erişim tokeni döner, gerekirse önce yeniler"""
        if self.yenileme_gerekli_mi(kimlik_bilgileri):
            kimlik_bilgileri = self.tokenlari_yenile(kimlik_bilgileri)
        return kimlik_bilgileri.erisim_tokeni.get_secret_value()

    def yenileme_gerekli_mi(self, kimlik_bilgileri: OAuth2Credentials) -> bool:
        """Verilen tokenların yenilenmesi gerekip gerekmediğini belirtir"""
        return (
            kimlik_bilgileri.erisim_tokeni_sona_erme_zamani is not None
            and kimlik_bilgileri.erisim_tokeni_sona_erme_zamani < int(time.time()) + 300
        )

    def varsayilan_kapsamlari_isle(self, kapsamlar: list[str]) -> list[str]:
        """Sağlayıcı için varsayılan kapsamları işler"""
        # Kapsamlar boşsa, sağlayıcı için varsayılan kapsamları kullan
        if not kapsamlar:
            logger.debug(
                f"{self.SAGLAYICI_ADI.value} sağlayıcısı için varsayılan kapsamlar kullanılıyor"
            )
            kapsamlar = self.VARSAYILAN_KAPSAMLAR
        return kapsamlar
