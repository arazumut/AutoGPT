from pydantic import BaseModel

from backend.data.block import (
    Block,
    BlockCategory,
    BlockManualWebhookConfig,
    BlockOutput,
    BlockSchema,
)
from backend.data.model import SchemaField
from backend.integrations.webhooks.compass import CompassWebhookType


class Transkripsiyon(BaseModel):
    metin: str
    konusmaci: str
    bitis: float
    baslangic: float
    sure: float


class TranskripsiyonVeriModeli(BaseModel):
    tarih: str
    transkripsiyon: str
    transkripsiyonlar: list[Transkripsiyon]


class CompassAITriggerBlok(Block):
    class Girdi(BlockSchema):
        yuk: TranskripsiyonVeriModeli = SchemaField(gizli=True)

    class Cikti(BlockSchema):
        transkripsiyon: str = SchemaField(
            aciklama="Compass transkripsiyonunun içeriği."
        )

    def __init__(self):
        super().__init__(
            id="9464a020-ed1d-49e1-990f-7f2ac924a2b7",
            aciklama="Bu blok, Compass transkripsiyonunun içeriğini çıktı olarak verecek.",
            kategoriler={BlockCategory.HARDWARE},
            girdi_skemasi=CompassAITriggerBlok.Girdi,
            cikti_skemasi=CompassAITriggerBlok.Cikti,
            webhook_konfig=BlockManualWebhookConfig(
                saglayici="compass",
                webhook_turu=CompassWebhookType.TRANSCRIPTION,
            ),
            test_girdisi=[
                {"girdi": "Merhaba, Dünya!"},
                {"girdi": "Merhaba, Dünya!", "veri": "Mevcut Veri"},
            ],
            # test_ciktisi=[
            #     ("cikti", "Merhaba, Dünya!"),  # Veri sağlanmadı, bu yüzden tetikleyici döndü
            #     ("cikti", "Mevcut Veri"),  # Veri sağlandı, bu yüzden veri döndü.
            # ],
        )

    def calistir(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        yield "transkripsiyon", girdi_verisi.yuk.transkripsiyon
