from typing import List, Optional
from pydantic import BaseModel
from backend.blocks.exa._auth import (
    ExaCredentials,
    ExaCredentialsField,
    ExaCredentialsInput,
)
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField
from backend.util.request import requests

class IcerikGetirmeAyarları(BaseModel):
    metin: Optional[dict] = SchemaField(
        description="Metin içerik ayarları",
        default={"maxCharacters": 1000, "includeHtmlTags": False},
        advanced=True,
    )
    vurgular: Optional[dict] = SchemaField(
        description="Vurgu ayarları",
        default={
            "numSentences": 3,
            "highlightsPerUrl": 3,
            "query": "",
        },
        advanced=True,
    )
    özet: Optional[dict] = SchemaField(
        description="Özet ayarları",
        default={"query": ""},
        advanced=True,
    )

class ExaIceriklerBlok(Block):
    class Girdi(BlockSchema):
        kimlik_bilgileri: ExaCredentialsInput = ExaCredentialsField()
        kimlikler: List[str] = SchemaField(
            description="Aramalardan elde edilen belge kimliklerinin dizisi",
        )
        icerikler: IcerikGetirmeAyarları = SchemaField(
            description="İçerik getirme ayarları",
            default=IcerikGetirmeAyarları(),
            advanced=True,
        )

    class Cikti(BlockSchema):
        sonuçlar: list = SchemaField(
            description="Belge içeriklerinin listesi",
            default=[],
        )

    def __init__(self):
        super().__init__(
            id="c52be83f-f8cd-4180-b243-af35f986b461",
            description="Exa'nın içerik API'sini kullanarak belge içeriklerini getirir",
            categories={BlockCategory.SEARCH},
            input_schema=ExaIceriklerBlok.Girdi,
            output_schema=ExaIceriklerBlok.Cikti,
        )

    def çalıştır(
        self, girdi_verisi: Girdi, *, kimlik_bilgileri: ExaCredentials, **kwargs
    ) -> BlockOutput:
        url = "https://api.exa.ai/contents"
        başlıklar = {
            "Content-Type": "application/json",
            "x-api-key": kimlik_bilgileri.api_key.get_secret_value(),
        }

        yük = {
            "ids": girdi_verisi.kimlikler,
            "text": girdi_verisi.icerikler.metin,
            "highlights": girdi_verisi.icerikler.vurgular,
            "summary": girdi_verisi.icerikler.özet,
        }

        try:
            yanıt = requests.post(url, headers=başlıklar, json=yük)
            yanıt.raise_for_status()
            veri = yanıt.json()
            yield "sonuçlar", veri.get("results", [])
        except Exception as e:
            yield "hata", str(e)
            yield "sonuçlar", []
