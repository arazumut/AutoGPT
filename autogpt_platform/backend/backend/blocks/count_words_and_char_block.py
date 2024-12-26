from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField

class KelimeKarakterSayisiBloku(Block):
    class Girdi(BlockSchema):
        metin: str = SchemaField(
            description="Kelime ve karakter sayısını saymak için giriş metni",
            placeholder="Metninizi buraya girin",
            advanced=False,
        )

    class Cikti(BlockSchema):
        kelime_sayisi: int = SchemaField(description="Giriş metnindeki kelime sayısı")
        karakter_sayisi: int = SchemaField(
            description="Giriş metnindeki karakter sayısı"
        )
        hata: str = SchemaField(
            description="Sayma işlemi başarısız olursa hata mesajı"
        )

    def __init__(self):
        super().__init__(
            id="ab2a782d-22cf-4587-8a70-55b59b3f9f90",
            description="Verilen bir metindeki kelime ve karakter sayısını sayar.",
            categories={BlockCategory.TEXT},
            input_schema=KelimeKarakterSayisiBloku.Girdi,
            output_schema=KelimeKarakterSayisiBloku.Cikti,
            test_input={"metin": "Merhaba, nasılsınız?"},
            test_output=[("kelime_sayisi", 3), ("karakter_sayisi", 19)],
        )

    def calistir(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        try:
            metin = girdi_verisi.metin
            kelime_sayisi = len(metin.split())
            karakter_sayisi = len(metin)

            yield "kelime_sayisi", kelime_sayisi
            yield "karakter_sayisi", karakter_sayisi

        except Exception as e:
            yield "hata", str(e)
