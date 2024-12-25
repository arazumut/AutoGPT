from datetime import datetime
from typing import List

from backend.blocks.exa._auth import (
    ExaCredentials,
    ExaCredentialsField,
    ExaCredentialsInput,
)
from backend.blocks.exa.helpers import ContentSettings
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField
from backend.util.request import requests


class ExaAramaBloğu(Block):
    class Girdi(BlockSchema):
        kimlik_bilgileri: ExaCredentialsInput = ExaCredentialsField()
        sorgu: str = SchemaField(description="Arama sorgusu")
        otomatik_öneri_kullan: bool = SchemaField(
            description="Otomatik öneri kullanılsın mı",
            default=True,
            advanced=True,
        )
        tür: str = SchemaField(
            description="Arama türü",
            default="",
            advanced=True,
        )
        kategori: str = SchemaField(
            description="Arama yapılacak kategori",
            default="",
            advanced=True,
        )
        sonuç_sayısı: int = SchemaField(
            description="Döndürülecek sonuç sayısı",
            default=10,
            advanced=True,
        )
        dahil_edilecek_alan_adları: List[str] = SchemaField(
            description="Aramada dahil edilecek alan adları",
            default=[],
        )
        hariç_tutulacak_alan_adları: List[str] = SchemaField(
            description="Aramada hariç tutulacak alan adları",
            default=[],
            advanced=True,
        )
        başlama_tarama_tarihi: datetime = SchemaField(
            description="Tarama içeriği için başlangıç tarihi",
        )
        bitiş_tarama_tarihi: datetime = SchemaField(
            description="Tarama içeriği için bitiş tarihi",
        )
        başlama_yayın_tarihi: datetime = SchemaField(
            description="Yayın içeriği için başlangıç tarihi",
        )
        bitiş_yayın_tarihi: datetime = SchemaField(
            description="Yayın içeriği için bitiş tarihi",
        )
        dahil_edilecek_metin: List[str] = SchemaField(
            description="Dahil edilecek metin desenleri",
            default=[],
            advanced=True,
        )
        hariç_tutulacak_metin: List[str] = SchemaField(
            description="Hariç tutulacak metin desenleri",
            default=[],
            advanced=True,
        )
        içerik_ayarları: ContentSettings = SchemaField(
            description="İçerik getirme ayarları",
            default=ContentSettings(),
            advanced=True,
        )

    class Çıktı(BlockSchema):
        sonuçlar: list = SchemaField(
            description="Arama sonuçlarının listesi",
            default=[],
        )

    def __init__(self):
        super().__init__(
            id="996cec64-ac40-4dde-982f-b0dc60a5824d",
            description="Exa'nın gelişmiş arama API'sini kullanarak webde arama yapar",
            categories={BlockCategory.SEARCH},
            input_schema=ExaAramaBloğu.Girdi,
            output_schema=ExaAramaBloğu.Çıktı,
        )

    def çalıştır(
        self, girdi_verisi: Girdi, *, kimlik_bilgileri: ExaCredentials, **kwargs
    ) -> BlockOutput:
        url = "https://api.exa.ai/search"
        başlıklar = {
            "Content-Type": "application/json",
            "x-api-key": kimlik_bilgileri.api_key.get_secret_value(),
        }

        yük = {
            "query": girdi_verisi.sorgu,
            "useAutoprompt": girdi_verisi.otomatik_öneri_kullan,
            "numResults": girdi_verisi.sonuç_sayısı,
            "contents": girdi_verisi.içerik_ayarları.dict(),
        }

        tarih_alanı_haritalama = {
            "başlama_tarama_tarihi": "startCrawlDate",
            "bitiş_tarama_tarihi": "endCrawlDate",
            "başlama_yayın_tarihi": "startPublishedDate",
            "bitiş_yayın_tarihi": "endPublishedDate",
        }

        # Tarihleri ekle
        for girdi_alanı, api_alanı in tarih_alanı_haritalama.items():
            değer = getattr(girdi_verisi, girdi_alanı, None)
            if değer:
                yük[api_alanı] = değer.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        isteğe_bağlı_alan_haritalama = {
            "tür": "type",
            "kategori": "category",
            "dahil_edilecek_alan_adları": "includeDomains",
            "hariç_tutulacak_alan_adları": "excludeDomains",
            "dahil_edilecek_metin": "includeText",
            "hariç_tutulacak_metin": "excludeText",
        }

        # Diğer alanları ekle
        for girdi_alanı, api_alanı in isteğe_bağlı_alan_haritalama.items():
            değer = getattr(girdi_verisi, girdi_alanı)
            if değer:  # Sadece boş olmayan değerleri ekle
                yük[api_alanı] = değer

        try:
            yanıt = requests.post(url, headers=başlıklar, json=yük)
            yanıt.raise_for_status()
            veri = yanıt.json()
            # Yanıttan sadece sonuçlar dizisini çıkar
            yield "sonuçlar", veri.get("results", [])
        except Exception as e:
            yield "hata", str(e)
            yield "sonuçlar", []
