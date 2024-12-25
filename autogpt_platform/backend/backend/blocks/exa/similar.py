from datetime import datetime
from typing import Any, List

from backend.blocks.exa._auth import (
    ExaCredentials,
    ExaCredentialsField,
    ExaCredentialsInput,
)
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField
from backend.util.request import requests

from .helpers import ContentSettings


class ExaBenzerBulBlok(Block):
    class Girdi(BlockSchema):
        kimlik_bilgileri: ExaCredentialsInput = ExaCredentialsField()
        url: str = SchemaField(
            description="Benzer bağlantıları bulmak istediğiniz URL"
        )
        sonuc_sayisi: int = SchemaField(
            description="Döndürülecek sonuç sayısı",
            default=10,
            advanced=True,
        )
        dahil_edilecek_alan_adlari: List[str] = SchemaField(
            description="Aramaya dahil edilecek alan adları",
            default=[],
            advanced=True,
        )
        hariç_tutulacak_alan_adlari: List[str] = SchemaField(
            description="Aramadan hariç tutulacak alan adları",
            default=[],
            advanced=True,
        )
        baslangic_tarama_tarihi: datetime = SchemaField(
            description="Tarama içeriği için başlangıç tarihi",
        )
        bitis_tarama_tarihi: datetime = SchemaField(
            description="Tarama içeriği için bitiş tarihi",
        )
        baslangic_yayin_tarihi: datetime = SchemaField(
            description="Yayınlanmış içerik için başlangıç tarihi",
        )
        bitis_yayin_tarihi: datetime = SchemaField(
            description="Yayınlanmış içerik için bitiş tarihi",
        )
        dahil_edilecek_metin: List[str] = SchemaField(
            description="Dahil edilecek metin desenleri (maksimum 1 dize, en fazla 5 kelime)",
            default=[],
            advanced=True,
        )
        hariç_tutulacak_metin: List[str] = SchemaField(
            description="Hariç tutulacak metin desenleri (maksimum 1 dize, en fazla 5 kelime)",
            default=[],
            advanced=True,
        )
        icerik_ayarları: ContentSettings = SchemaField(
            description="İçerik alma ayarları",
            default=ContentSettings(),
            advanced=True,
        )

    class Cikti(BlockSchema):
        sonuclar: List[Any] = SchemaField(
            description="Başlık, URL, yayın tarihi, yazar ve puan ile benzer belgelerin listesi",
            default=[],
        )

    def __init__(self):
        super().__init__(
            id="5e7315d1-af61-4a0c-9350-7c868fa7438a",
            description="Exa'nın findSimilar API'sini kullanarak benzer bağlantıları bulur",
            categories={BlockCategory.SEARCH},
            input_schema=ExaBenzerBulBlok.Girdi,
            output_schema=ExaBenzerBulBlok.Cikti,
        )

    def calistir(
        self, girdi_verisi: Girdi, *, kimlik_bilgileri: ExaCredentials, **kwargs
    ) -> BlockOutput:
        url = "https://api.exa.ai/findSimilar"
        basliklar = {
            "Content-Type": "application/json",
            "x-api-key": kimlik_bilgileri.api_key.get_secret_value(),
        }

        yuk = {
            "url": girdi_verisi.url,
            "numResults": girdi_verisi.sonuc_sayisi,
            "contents": girdi_verisi.icerik_ayarları.dict(),
        }

        opsiyonel_alan_esleme = {
            "dahil_edilecek_alan_adlari": "includeDomains",
            "hariç_tutulacak_alan_adlari": "excludeDomains",
            "dahil_edilecek_metin": "includeText",
            "hariç_tutulacak_metin": "excludeText",
        }

        # Değerleri olan opsiyonel alanları ekle
        for girdi_alanı, api_alanı in opsiyonel_alan_esleme.items():
            deger = getattr(girdi_verisi, girdi_alanı)
            if deger:  # Sadece boş olmayan değerleri ekle
                yuk[api_alanı] = deger

        tarih_alan_esleme = {
            "baslangic_tarama_tarihi": "startCrawlDate",
            "bitis_tarama_tarihi": "endCrawlDate",
            "baslangic_yayin_tarihi": "startPublishedDate",
            "bitis_yayin_tarihi": "endPublishedDate",
        }

        # Tarihleri ekle
        for girdi_alanı, api_alanı in tarih_alan_esleme.items():
            deger = getattr(girdi_verisi, girdi_alanı, None)
            if deger:
                yuk[api_alanı] = deger.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        try:
            yanit = requests.post(url, headers=basliklar, json=yuk)
            yanit.raise_for_status()
            veri = yanit.json()
            yield "sonuclar", veri.get("results", [])
        except Exception as e:
            yield "hata", str(e)
            yield "sonuclar", []
