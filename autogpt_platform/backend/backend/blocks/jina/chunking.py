from backend.blocks.jina._auth import (
    JinaCredentials,
    JinaCredentialsField,
    JinaCredentialsInput,
)
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField
from backend.util.request import requests


class JinaParçalamaBloğu(Block):
    class Girdi(BlockSchema):
        metinler: list = SchemaField(description="Parçalanacak metinlerin listesi")

        kimlik_bilgileri: JinaCredentialsInput = JinaCredentialsField()
        max_parça_uzunluğu: int = SchemaField(
            description="Her parçanın maksimum uzunluğu", default=1000
        )
        token_dön: bool = SchemaField(
            description="Token bilgilerini döndürüp döndürmeyeceği", default=False
        )

    class Çıktı(BlockSchema):
        parçalar: list = SchemaField(description="Parçalanmış metinlerin listesi")
        tokenler: list = SchemaField(
            description="Her parça için token bilgileri listesi", optional=True
        )

    def __init__(self):
        super().__init__(
            id="806fb15e-830f-4796-8692-557d300ff43c",
            description="Jina AI'nın segmentasyon servisini kullanarak metinleri parçalara ayırır",
            categories={BlockCategory.AI, BlockCategory.TEXT},
            input_schema=JinaParçalamaBloğu.Girdi,
            output_schema=JinaParçalamaBloğu.Çıktı,
        )

    def çalıştır(
        self, girdi_verisi: Girdi, *, kimlik_bilgileri: JinaCredentials, **kwargs
    ) -> BlockOutput:
        url = "https://segment.jina.ai/"
        başlıklar = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {kimlik_bilgileri.api_key.get_secret_value()}",
        }

        tüm_parçalar = []
        tüm_tokenler = []

        for metin in girdi_verisi.metinler:
            veri = {
                "content": metin,
                "return_tokens": str(girdi_verisi.token_dön).lower(),
                "return_chunks": "true",
                "max_chunk_length": str(girdi_verisi.max_parça_uzunluğu),
            }

            yanıt = requests.post(url, headers=başlıklar, json=veri)
            sonuç = yanıt.json()

            tüm_parçalar.extend(sonuç.get("chunks", []))
            if girdi_verisi.token_dön:
                tüm_tokenler.extend(sonuç.get("tokens", []))

        yield "parçalar", tüm_parçalar
        if girdi_verisi.token_dön:
            yield "tokenler", tüm_tokenler
