from groq._utils._utils import quote

from backend.blocks.jina._auth import (
    TEST_CREDENTIALS,
    TEST_CREDENTIALS_INPUT,
    JinaCredentials,
    JinaCredentialsField,
    JinaCredentialsInput,
)
from backend.blocks.search import GetRequest
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class WebdeAramaYapBlok(Block, GetRequest):
    class Girdi(BlockSchema):
        kimlik_bilgileri: JinaCredentialsInput = JinaCredentialsField()
        sorgu: str = SchemaField(description="Webde arama yapmak için arama sorgusu")

    class Çıktı(BlockSchema):
        sonuçlar: str = SchemaField(
            description="İlk 5 URL'den içerik dahil arama sonuçları"
        )
        hata: str = SchemaField(description="Arama başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="87840993-2053-44b7-8da4-187ad4ee518c",
            description="Bu blok, verilen arama sorgusu için internette arama yapar.",
            categories={BlockCategory.SEARCH},
            input_schema=WebdeAramaYapBlok.Girdi,
            output_schema=WebdeAramaYapBlok.Çıktı,
            test_input={
                "kimlik_bilgileri": TEST_CREDENTIALS_INPUT,
                "sorgu": "Yapay Zeka",
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=("sonuçlar", "arama içeriği"),
            test_mock={"get_request": lambda *args, **kwargs: "arama içeriği"},
        )

    def çalıştır(
        self, girdi_verisi: Girdi, *, kimlik_bilgileri: JinaCredentials, **kwargs
    ) -> BlockOutput:
        # Arama sorgusunu kodla
        kodlanmış_sorgu = quote(girdi_verisi.sorgu)
        başlıklar = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {kimlik_bilgileri.api_key.get_secret_value()}",
        }

        # Jina Arama URL'sini kodlanmış sorguya ekle
        jina_arama_url = f"https://s.jina.ai/{kodlanmış_sorgu}"
        sonuçlar = self.get_request(jina_arama_url, headers=başlıklar, json=False)

        # Arama sonuçlarını çıktı olarak ver
        yield "sonuçlar", sonuçlar


class WebSitesiİçeriğiÇıkarBlok(Block, GetRequest):
    class Girdi(BlockSchema):
        kimlik_bilgileri: JinaCredentialsInput = JinaCredentialsField()
        url: str = SchemaField(description="İçeriği kazımak için URL")
        ham_içerik: bool = SchemaField(
            default=False,
            title="Ham İçerik",
            description="İçeriği ham olarak mı kazıyacağınızı yoksa Jina-ai Reader kullanarak mı kazıyacağınızı belirtir",
            advanced=True,
        )

    class Çıktı(BlockSchema):
        içerik: str = SchemaField(description="Verilen URL'den kazınan içerik")
        hata: str = SchemaField(
            description="İçerik alınamazsa hata mesajı"
        )

    def __init__(self):
        super().__init__(
            id="436c3984-57fd-4b85-8e9a-459b356883bd",
            description="Bu blok, verilen web URL'sinden içerik kazır.",
            categories={BlockCategory.SEARCH},
            input_schema=WebSitesiİçeriğiÇıkarBlok.Girdi,
            output_schema=WebSitesiİçeriğiÇıkarBlok.Çıktı,
            test_input={
                "url": "https://tr.wikipedia.org/wiki/Yapay_zeka",
                "kimlik_bilgileri": TEST_CREDENTIALS_INPUT,
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=("içerik", "kazınan içerik"),
            test_mock={"get_request": lambda *args, **kwargs: "kazınan içerik"},
        )

    def çalıştır(
        self, girdi_verisi: Girdi, *, kimlik_bilgileri: JinaCredentials, **kwargs
    ) -> BlockOutput:
        if girdi_verisi.ham_içerik:
            url = girdi_verisi.url
            başlıklar = {}
        else:
            url = f"https://r.jina.ai/{girdi_verisi.url}"
            başlıklar = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {kimlik_bilgileri.api_key.get_secret_value()}",
            }

        içerik = self.get_request(url, json=False, headers=başlıklar)
        yield "içerik", içerik
