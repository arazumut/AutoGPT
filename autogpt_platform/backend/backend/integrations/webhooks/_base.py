import logging
import secrets
from abc import ABC, abstractmethod
from typing import ClassVar, Generic, Optional, TypeVar
from uuid import uuid4

from fastapi import Request
from strenum import StrEnum

from backend.data import integrations
from backend.data.model import Credentials
from backend.integrations.providers import ProviderName
from backend.integrations.webhooks.utils import webhook_ingress_url
from backend.util.exceptions import MissingConfigError
from backend.util.settings import Config

logger = logging.getLogger(__name__)
app_config = Config()

WT = TypeVar("WT", bound=StrEnum)


class BaseWebhooksManager(ABC, Generic[WT]):
    PROVIDER_NAME: ClassVar[ProviderName]

    WebhookType: WT

    async def uygun_otomatik_webhooku_al(
        self,
        kullanici_id: str,
        kimlik_bilgileri: Credentials,
        webhook_tipi: WT,
        kaynak: str,
        olaylar: list[str],
    ) -> integrations.Webhook:
        if not app_config.platform_base_url:
            raise MissingConfigError(
                "PLATFORM_BASE_URL, Webhook işlevselliğini kullanmak için ayarlanmalıdır"
            )

        if webhook := await integrations.find_webhook_by_credentials_and_props(
            kimlik_bilgileri.id, webhook_tipi, kaynak, olaylar
        ):
            return webhook
        return await self._webhook_olustur(
            kullanici_id, webhook_tipi, olaylar, kaynak, kimlik_bilgileri
        )

    async def manuel_webhook_al(
        self,
        kullanici_id: str,
        grafik_id: str,
        webhook_tipi: WT,
        olaylar: list[str],
    ):
        if mevcut_webhook := await integrations.find_webhook_by_graph_and_props(
            grafik_id, self.PROVIDER_NAME, webhook_tipi, olaylar
        ):
            return mevcut_webhook
        return await self._webhook_olustur(
            kullanici_id,
            webhook_tipi,
            olaylar,
            kaydet=False,
        )

    async def bos_webhooku_temizle(
        self, webhook_id: str, kimlik_bilgileri: Optional[Credentials]
    ) -> bool:
        webhook = await integrations.get_webhook(webhook_id)
        if webhook.attached_nodes is None:
            raise ValueError("Bağlı düğümleri içeren webhook alınırken hata oluştu")
        if webhook.attached_nodes:
            # Kullanımda ise webhooku temizleme
            return False

        if kimlik_bilgileri:
            await self._webhooku_deregister_et(webhook, kimlik_bilgileri)
        await integrations.delete_webhook(webhook.id)
        return True

    @classmethod
    @abstractmethod
    async def payload_dogrula(
        cls, webhook: integrations.Webhook, istek: Request
    ) -> tuple[dict, str]:
        """
        Gelen bir webhook isteğini doğrular ve yükünü ve türünü döndürür.

        Parametreler:
            webhook: Sistemimizde yapılandırılmış webhook ve özelliklerini temsil eden nesne.
            istek: Gelen FastAPI `Request`

        Döndürür:
            dict: Doğrulanmış yük
            str: Yük ile ilişkili olay türü
        """

    async def ping_tetikle(
        self, webhook: integrations.Webhook, kimlik_bilgileri: Credentials | None
    ) -> None:
        """
        Belirtilen webhooka bir ping tetikler.

        Hata:
            NotImplementedError: Sağlayıcı pinglemeyi desteklemiyorsa
        """
        raise NotImplementedError(f"{self.__class__.__name__} pinglemeyi desteklemiyor")

    @abstractmethod
    async def _webhooku_kaydet(
        self,
        kimlik_bilgileri: Credentials,
        webhook_tipi: WT,
        kaynak: str,
        olaylar: list[str],
        giris_url: str,
        gizli_anahtar: str,
    ) -> tuple[str, dict]:
        """
        Sağlayıcı ile yeni bir webhook kaydeder.

        Parametreler:
            kimlik_bilgileri: Webhook oluşturmak için kullanılacak kimlik bilgileri
            webhook_tipi: Oluşturulacak sağlayıcıya özgü webhook türü
            kaynak: Olayları almak için kaynak
            olaylar: Abone olunacak olaylar
            giris_url: Webhook yükleri için giriş URL'si
            gizli_anahtar: Webhook yüklerini doğrulamak için kullanılan gizli anahtar

        Döndürür:
            str: Sağlayıcı tarafından atanan Webhook ID'si
            dict: Webhook için sağlayıcıya özgü yapılandırma
        """
        ...

    @abstractmethod
    async def _webhooku_deregister_et(
        self, webhook: integrations.Webhook, kimlik_bilgileri: Credentials
    ) -> None:
        ...

    async def _webhook_olustur(
        self,
        kullanici_id: str,
        webhook_tipi: WT,
        olaylar: list[str],
        kaynak: str = "",
        kimlik_bilgileri: Optional[Credentials] = None,
        kaydet: bool = True,
    ) -> integrations.Webhook:
        if not app_config.platform_base_url:
            raise MissingConfigError(
                "PLATFORM_BASE_URL, Webhook işlevselliğini kullanmak için ayarlanmalıdır"
            )

        id = str(uuid4())
        gizli_anahtar = secrets.token_hex(32)
        saglayici_adi = self.PROVIDER_NAME
        giris_url = webhook_ingress_url(provider_name=saglayici_adi, webhook_id=id)
        if kaydet:
            if not kimlik_bilgileri:
                raise TypeError("kaydet = True ise kimlik bilgileri gereklidir")
            saglayici_webhook_id, config = await self._webhooku_kaydet(
                kimlik_bilgileri, webhook_tipi, kaynak, olaylar, giris_url, gizli_anahtar
            )
        else:
            saglayici_webhook_id, config = "", {}

        return await integrations.create_webhook(
            integrations.Webhook(
                id=id,
                user_id=kullanici_id,
                provider=saglayici_adi,
                credentials_id=kimlik_bilgileri.id if kimlik_bilgileri else "",
                webhook_type=webhook_tipi,
                resource=kaynak,
                events=olaylar,
                provider_webhook_id=saglayici_webhook_id,
                config=config,
                secret=gizli_anahtar,
            )
        )
