import logging

from fastapi import Request
from strenum import StrEnum

from backend.data import integrations
from backend.integrations.providers import ProviderName

from ._manual_base import ManualWebhookManagerBase

logger = logging.getLogger(__name__)


class CompassWebhookType(StrEnum):
    TRANSKRİPSİYON = "transcription"
    GÖREV = "task"


class CompassWebhookManager(ManualWebhookManagerBase):
    SAĞLAYICI_ADI = ProviderName.COMPASS
    WebhookTipi = CompassWebhookType

    @classmethod
    async def yükü_doğrula(
        cls, webhook: integrations.Webhook, istek: Request
    ) -> tuple[dict, str]:
        yük = await istek.json()
        olay_tipi = CompassWebhookType.TRANSKRİPSİYON  # şu anda tek tip

        return yük, olay_tipi
