import logging
from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING

from autogpt_libs.utils.synchronize import RedisKeyedMutex
from redis.lock import Lock as RedisLock

from backend.data import redis
from backend.data.model import Credentials
from backend.integrations.credentials_store import IntegrationCredentialsStore
from backend.integrations.oauth import HANDLERS_BY_NAME
from backend.util.exceptions import MissingConfigError
from backend.util.settings import Settings

if TYPE_CHECKING:
    from backend.integrations.oauth import BaseOAuthHandler

logger = logging.getLogger(__name__)
settings = Settings()


class EntegrasyonKimlikBilgileriYöneticisi:
    """
    Entegrasyon kimlik bilgilerinin yaşam döngüsünü yönetir.
    - Gerektiğinde istenen kimlik bilgilerini otomatik olarak yeniler.
    - Sistem genelinde tutarlılığı sağlamak ve kullanımda olan tokenlerin geçersiz kılınmasını önlemek için kilitleme mekanizmaları kullanır.

    ### ⚠️ Dikkat
    `acquire(..)` ile, kimlik bilgileri aynı anda yalnızca bir yerde kullanılabilir (örneğin, bir blok yürütme).

    ### Kilitleme mekanizması
    - Kimlik bilgilerini *almak*, saklanan kimlik bilgilerinin yenilenmesiyle (= *geçersiz kılma* + *değiştirme*) sonuçlanabileceğinden, *almak* okuma/yazma erişimi gerektiren bir işlemdir.
    - Bir tokenin yenilenmesi gerekip gerekmediğini kontrol etmek, aynı kimlik bilgilerine aynı anda erişmeye çalışan birden fazla yürütme sırasında gereksiz ardışık yenilemeleri önlemek için ek bir `refresh` kapsamlı kilide tabidir.
    - Kimlik bilgilerini kullanımda iken kilitlemeliyiz, böylece sistemin başka bir kısmı tarafından yenilenirken geçersiz kılınmalarını önleriz.
    - `!time_sensitive` kilidi `acquire(..)` içinde, *güncellemenin* kimlik bilgilerini *almaktan* öncelikli olduğu iki aşamalı bir kilitleme mekanizmasının parçasıdır.
      Bu, uzun bir bekleyen *alma* istekleri kuyruğunun, önemli kimlik bilgisi yenilemelerini veya kullanıcı tarafından başlatılan güncellemeleri engellemesini önlemek içindir.

    Aynı anda birden fazla okuyucunun veya tek bir yazarın erişimine izin veren bir okuyucu/yazar kilitleme sistemi uygulamak mümkündür, ancak bu mekanizmaya çok fazla karmaşıklık katacaktır. Mevcut ("basit") mekanizmanın, uygulanmaya değer olacak kadar gecikmeye neden olmasını beklemiyorum.
    """

    def __init__(self):
        redis_conn = redis.get_redis()
        self._locks = RedisKeyedMutex(redis_conn)
        self.store = IntegrationCredentialsStore()

    def oluştur(self, kullanıcı_id: str, kimlik_bilgileri: Credentials) -> None:
        return self.store.add_creds(kullanıcı_id, kimlik_bilgileri)

    def var_mı(self, kullanıcı_id: str, kimlik_bilgileri_id: str) -> bool:
        return self.store.get_creds_by_id(kullanıcı_id, kimlik_bilgileri_id) is not None

    def al(
        self, kullanıcı_id: str, kimlik_bilgileri_id: str, kilit: bool = True
    ) -> Credentials | None:
        kimlik_bilgileri = self.store.get_creds_by_id(kullanıcı_id, kimlik_bilgileri_id)
        if not kimlik_bilgileri:
            return None

        # OAuth kimlik bilgilerini gerektiğinde yenile
        if kimlik_bilgileri.type == "oauth2" and kimlik_bilgileri.access_token_expires_at:
            logger.debug(
                f"Kimlik Bilgileri #{kimlik_bilgileri.id} şu tarihte sona eriyor: "
                f"{datetime.fromtimestamp(kimlik_bilgileri.access_token_expires_at)}; "
                f"mevcut zaman {datetime.now()}"
            )

            with self._kilitli(kullanıcı_id, kimlik_bilgileri_id, "refresh"):
                oauth_handler = _sağlayıcı_oauth_handler_al(kimlik_bilgileri.provider)
                if oauth_handler.yenileme_gerekli_mi(kimlik_bilgileri):
                    logger.debug(
                        f"'{kimlik_bilgileri.provider}' kimlik bilgileri #{kimlik_bilgileri.id} yenileniyor"
                    )
                    _kilit = None
                    if kilit:
                        # Kimlik bilgileri başka bir yerde kullanımda değilken bekle
                        _kilit = self._kilit_al(kullanıcı_id, kimlik_bilgileri_id)

                    yeni_kimlik_bilgileri = oauth_handler.tokenleri_yenile(kimlik_bilgileri)
                    self.store.update_creds(kullanıcı_id, yeni_kimlik_bilgileri)
                    if _kilit:
                        _kilit.release()

                    kimlik_bilgileri = yeni_kimlik_bilgileri
        else:
            logger.debug(f"Kimlik Bilgileri #{kimlik_bilgileri.id} hiç sona ermiyor")

        return kimlik_bilgileri

    def edin(
        self, kullanıcı_id: str, kimlik_bilgileri_id: str
    ) -> tuple[Credentials, RedisLock]:
        """
        ⚠️ UYARI: bu, kimlik bilgilerini sistem genelinde kilitler ve kilit serbest bırakılana kadar başka yerlerde edinme ve güncellemeyi engeller.
        Daha fazla bilgi için sınıf docstring'ine bakın.
        """
        # Düşük öncelikli (!time_sensitive) bir kilitleme kuyruğu kullanarak genel kilidin üstünde, token yenileme/güncelleme için öncelikli erişim sağlar.
        with self._kilitli(kullanıcı_id, kimlik_bilgileri_id, "!time_sensitive"):
            kilit = self._kilit_al(kullanıcı_id, kimlik_bilgileri_id)
        kimlik_bilgileri = self.al(kullanıcı_id, kimlik_bilgileri_id, kilit=False)
        if not kimlik_bilgileri:
            raise ValueError(
                f"Kullanıcı #{kullanıcı_id} için Kimlik Bilgileri #{kimlik_bilgileri_id} bulunamadı"
            )
        return kimlik_bilgileri, kilit

    def güncelle(self, kullanıcı_id: str, güncellenmiş: Credentials) -> None:
        with self._kilitli(kullanıcı_id, güncellenmiş.id):
            self.store.update_creds(kullanıcı_id, güncellenmiş)

    def sil(self, kullanıcı_id: str, kimlik_bilgileri_id: str) -> None:
        with self._kilitli(kullanıcı_id, kimlik_bilgileri_id):
            self.store.delete_creds_by_id(kullanıcı_id, kimlik_bilgileri_id)

    # -- Kilitleme yardımcıları -- #

    def _kilit_al(self, kullanıcı_id: str, kimlik_bilgileri_id: str, *args: str) -> RedisLock:
        anahtar = (
            f"kullanıcı:{kullanıcı_id}",
            f"kimlik_bilgileri:{kimlik_bilgileri_id}",
            *args,
        )
        return self._locks.acquire(anahtar)

    @contextmanager
    def _kilitli(self, kullanıcı_id: str, kimlik_bilgileri_id: str, *args: str):
        kilit = self._kilit_al(kullanıcı_id, kimlik_bilgileri_id, *args)
        try:
            yield
        finally:
            kilit.release()

    def tüm_kilitleri_serbest_bırak(self):
        """Tüm kilitlerin serbest bırakıldığından emin olmak için bu işlemi süreç sonlandırmada çağırın"""
        self._locks.release_all_locks()
        self.store.locks.release_all_locks()


def _sağlayıcı_oauth_handler_al(sağlayıcı_adı: str) -> "BaseOAuthHandler":
    if sağlayıcı_adı not in HANDLERS_BY_NAME:
        raise KeyError(f"Bilinmeyen sağlayıcı '{sağlayıcı_adı}'")

    client_id = getattr(settings.secrets, f"{sağlayıcı_adı}_client_id")
    client_secret = getattr(settings.secrets, f"{sağlayıcı_adı}_client_secret")
    if not (client_id and client_secret):
        raise MissingConfigError(
            f"'{sağlayıcı_adı}' sağlayıcısı ile entegrasyon yapılandırılmamış",
        )

    handler_class = HANDLERS_BY_NAME[sağlayıcı_adı]
    frontend_base_url = (
        settings.config.frontend_base_url or settings.config.platform_base_url
    )
    return handler_class(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=f"{frontend_base_url}/auth/integrations/oauth_callback",
    )
