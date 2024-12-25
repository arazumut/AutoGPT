from enum import Enum
from typing import Any

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class KarsilastirmaOperatoru(Enum):
    ESIT = "=="
    ESIT_DEGIL = "!="
    BUYUK = ">"
    KUCUK = "<"
    BUYUK_ESIT = ">="
    KUCUK_ESIT = "<="


class KosulBloku(Block):
    class Girdi(BlockSchema):
        deger1: Any = SchemaField(
            description="Karşılaştırma için ilk değeri girin",
            placeholder="Örneğin: 10 veya 'merhaba' veya True",
        )
        operator: KarsilastirmaOperatoru = SchemaField(
            description="Karşılaştırma operatörünü seçin",
            placeholder="Bir operatör seçin",
        )
        deger2: Any = SchemaField(
            description="Karşılaştırma için ikinci değeri girin",
            placeholder="Örneğin: 20 veya 'dünya' veya False",
        )
        evet_degeri: Any = SchemaField(
            description="(Opsiyonel) Koşul doğruysa çıkış değeri. Sağlanmazsa, deger1 kullanılacak.",
            placeholder="Deger1 kullanmak için boş bırakın veya belirli bir değer girin",
            default=None,
        )
        hayir_degeri: Any = SchemaField(
            description="(Opsiyonel) Koşul yanlışsa çıkış değeri. Sağlanmazsa, deger1 kullanılacak.",
            placeholder="Deger1 kullanmak için boş bırakın veya belirli bir değer girin",
            default=None,
        )

    class Cikti(BlockSchema):
        sonuc: bool = SchemaField(
            description="Koşul değerlendirmesinin sonucu (True veya False)"
        )
        evet_ciktisi: Any = SchemaField(
            description="Koşul doğruysa çıkış değeri"
        )
        hayir_ciktisi: Any = SchemaField(
            description="Koşul yanlışsa çıkış değeri"
        )

    def __init__(self):
        super().__init__(
            id="715696a0-e1da-45c8-b209-c2fa9c3b0be6",
            input_schema=KosulBloku.Girdi,
            output_schema=KosulBloku.Cikti,
            description="Karşılaştırma operatörlerine dayalı koşullu mantığı işler",
            categories={BlockCategory.LOGIC},
            test_input={
                "deger1": 10,
                "operator": KarsilastirmaOperatoru.BUYUK.value,
                "deger2": 5,
                "evet_degeri": "Büyük",
                "hayir_degeri": "Büyük değil",
            },
            test_output=[
                ("sonuc", True),
                ("evet_ciktisi", "Büyük"),
            ],
        )

    def calistir(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        operator = girdi_verisi.operator

        deger1 = girdi_verisi.deger1
        if isinstance(deger1, str):
            try:
                deger1 = float(deger1.strip())
            except ValueError:
                deger1 = deger1.strip()

        deger2 = girdi_verisi.deger2
        if isinstance(deger2, str):
            try:
                deger2 = float(deger2.strip())
            except ValueError:
                deger2 = deger2.strip()

        evet_degeri = girdi_verisi.evet_degeri if girdi_verisi.evet_degeri is not None else deger1
        hayir_degeri = girdi_verisi.hayir_degeri if girdi_verisi.hayir_degeri is not None else deger2

        karsilastirma_fonksiyonlari = {
            KarsilastirmaOperatoru.ESIT: lambda a, b: a == b,
            KarsilastirmaOperatoru.ESIT_DEGIL: lambda a, b: a != b,
            KarsilastirmaOperatoru.BUYUK: lambda a, b: a > b,
            KarsilastirmaOperatoru.KUCUK: lambda a, b: a < b,
            KarsilastirmaOperatoru.BUYUK_ESIT: lambda a, b: a >= b,
            KarsilastirmaOperatoru.KUCUK_ESIT: lambda a, b: a <= b,
        }

        sonuc = karsilastirma_fonksiyonlari[operator](deger1, deger2)

        yield "sonuc", sonuc

        if sonuc:
            yield "evet_ciktisi", evet_degeri
        else:
            yield "hayir_ciktisi", hayir_degeri
