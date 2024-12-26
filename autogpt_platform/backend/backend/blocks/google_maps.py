from typing import Literal

import googlemaps
from pydantic import BaseModel, SecretStr

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
)
from backend.integrations.providers import ProviderName

# Test için kullanılan API anahtarı
TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="google_maps",
    api_key=SecretStr("mock-google-maps-api-key"),
    title="Mock Google Maps API key",
    expires_at=None,
)
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.type,
}

# Yer bilgilerini tutan model
class Yer(BaseModel):
    isim: str
    adres: str
    telefon: str
    puan: float
    yorum_sayisi: int
    web_sitesi: str

# Google Maps arama bloğu
class GoogleMapsAramaBlogu(Block):
    class Input(BlockSchema):
        kimlik_bilgileri: CredentialsMetaInput[
            Literal[ProviderName.GOOGLE_MAPS], Literal["api_key"]
        ] = CredentialsField(description="Google Maps API Anahtarı")
        sorgu: str = SchemaField(
            description="Yerel işletmeler için arama sorgusu",
            placeholder="örneğin, 'New York'ta restoranlar'",
        )
        yaricap: int = SchemaField(
            description="Arama yarıçapı (maksimum 50000 metre)",
            default=5000,
            ge=1,
            le=50000,
        )
        maksimum_sonuclar: int = SchemaField(
            description="Döndürülecek maksimum sonuç sayısı (maksimum 60)",
            default=20,
            ge=1,
            le=60,
        )

    class Output(BlockSchema):
        yer: Yer = SchemaField(description="Bulunan yer")
        hata: str = SchemaField(description="Arama başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
            description="Bu blok Google Maps API kullanarak yerel işletmeleri arar.",
            categories={BlockCategory.SEARCH},
            input_schema=GoogleMapsAramaBlogu.Input,
            output_schema=GoogleMapsAramaBlogu.Output,
            test_input={
                "kimlik_bilgileri": TEST_CREDENTIALS_INPUT,
                "sorgu": "new york'ta restoranlar",
                "yaricap": 5000,
                "maksimum_sonuclar": 5,
            },
            test_output=[
                (
                    "yer",
                    {
                        "isim": "Test Restoran",
                        "adres": "123 Test St, New York, NY 10001",
                        "telefon": "+1 (555) 123-4567",
                        "puan": 4.5,
                        "yorum_sayisi": 100,
                        "web_sitesi": "https://testrestaurant.com",
                    },
                ),
            ],
            test_mock={
                "arama_yerleri": lambda *args, **kwargs: [
                    {
                        "isim": "Test Restoran",
                        "adres": "123 Test St, New York, NY 10001",
                        "telefon": "+1 (555) 123-4567",
                        "puan": 4.5,
                        "yorum_sayisi": 100,
                        "web_sitesi": "https://testrestaurant.com",
                    }
                ]
            },
            test_credentials=TEST_CREDENTIALS,
        )

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        yerler = self.arama_yerleri(
            credentials.api_key,
            input_data.sorgu,
            input_data.yaricap,
            input_data.maksimum_sonuclar,
        )
        for yer in yerler:
            yield "yer", yer

    def arama_yerleri(self, api_key: SecretStr, sorgu, yaricap, maksimum_sonuclar):
        client = googlemaps.Client(key=api_key.get_secret_value())
        return self._arama_yerleri(client, sorgu, yaricap, maksimum_sonuclar)

    def _arama_yerleri(self, client, sorgu, yaricap, maksimum_sonuclar):
        sonuçlar = []
        sonraki_sayfa_tokeni = None
        while len(sonuçlar) < maksimum_sonuclar:
            yanit = client.places(
                query=sorgu,
                radius=yaricap,
                page_token=sonraki_sayfa_tokeni,
            )
            for yer in yanit["results"]:
                if len(sonuçlar) >= maksimum_sonuclar:
                    break
                yer_detaylari = client.place(yer["place_id"])["result"]
                sonuçlar.append(
                    Yer(
                        isim=yer_detaylari.get("name", ""),
                        adres=yer_detaylari.get("formatted_address", ""),
                        telefon=yer_detaylari.get("formatted_phone_number", ""),
                        puan=yer_detaylari.get("rating", 0),
                        yorum_sayisi=yer_detaylari.get("user_ratings_total", 0),
                        web_sitesi=yer_detaylari.get("website", ""),
                    )
                )
            sonraki_sayfa_tokeni = yanit.get("next_page_token")
            if not sonraki_sayfa_tokeni:
                break
        return sonuçlar
