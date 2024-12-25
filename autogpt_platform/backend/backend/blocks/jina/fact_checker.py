from urllib.parse import quote

import requests

from backend.blocks.jina._auth import (
    JinaCredentials,
    JinaCredentialsField,
    JinaCredentialsInput,
)
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class GercekKontrolBloku(Block):
    class Girdi(BlockSchema):
        ifade: str = SchemaField(
            description="Gerçekliği kontrol edilecek ifade"
        )
        kimlik_bilgileri: JinaCredentialsInput = JinaCredentialsField()

    class Cikti(BlockSchema):
        gerceklik: float = SchemaField(
            description="İfadenin gerçeklik puanı"
        )
        sonuc: bool = SchemaField(description="Gerçeklik kontrolünün sonucu")
        sebep: str = SchemaField(description="Gerçeklik sonucunun sebebi")
        hata: str = SchemaField(description="Kontrol başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="d38b6c5e-9968-4271-8423-6cfe60d6e7e6",
            description="Bu blok, verilen ifadenin gerçekliğini Jina AI'nin Grounding API'sini kullanarak kontrol eder.",
            categories={BlockCategory.SEARCH},
            input_schema=GercekKontrolBloku.Girdi,
            output_schema=GercekKontrolBloku.Cikti,
        )

    def calistir(
        self, girdi_verisi: Girdi, *, kimlik_bilgileri: JinaCredentials, **kwargs
    ) -> BlockOutput:
        kodlanmis_ifade = quote(girdi_verisi.ifade)
        url = f"https://g.jina.ai/{kodlanmis_ifade}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {kimlik_bilgileri.api_key.get_secret_value()}",
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "data" in data:
            data = data["data"]
            yield "gerceklik", data["factuality"]
            yield "sonuc", data["result"]
            yield "sebep", data["reason"]
        else:
            raise RuntimeError(f"Beklenen 'data' anahtarı yanıt içinde bulunamadı: {data}")

