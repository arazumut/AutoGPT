import operator
from enum import Enum
from typing import Any

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class Islem(Enum):
    TOPLA = "Topla"
    CIKAR = "Çıkar"
    CARP = "Çarp"
    BOL = "Böl"
    US = "Üs"


class HesapMakinesiBlok(Block):
    class Girdi(BlockSchema):
        islem: Islem = SchemaField(
            description="Yapmak istediğiniz matematiksel işlemi seçin",
            placeholder="Bir işlem seçin",
        )
        a: float = SchemaField(
            description="Birinci sayıyı girin (A)", placeholder="Örneğin: 10"
        )
        b: float = SchemaField(
            description="İkinci sayıyı girin (B)", placeholder="Örneğin: 5"
        )
        sonucu_yuvarla: bool = SchemaField(
            description="Sonucu tam sayıya yuvarlamak ister misiniz?",
            default=False,
        )

    class Cikti(BlockSchema):
        sonuc: float = SchemaField(description="Hesaplamanızın sonucu")

    def __init__(self):
        super().__init__(
            id="b1ab9b19-67a6-406d-abf5-2dba76d00c79",
            input_schema=HesapMakinesiBlok.Girdi,
            output_schema=HesapMakinesiBlok.Cikti,
            description="İki sayı üzerinde matematiksel bir işlem gerçekleştirir.",
            categories={BlockCategory.LOGIC},
            test_input={
                "islem": Islem.TOPLA.value,
                "a": 10.0,
                "b": 5.0,
                "sonucu_yuvarla": False,
            },
            test_output=[
                ("sonuc", 15.0),
            ],
        )

    def run(self, input_data: Girdi, **kwargs) -> BlockOutput:
        islem = input_data.islem
        a = input_data.a
        b = input_data.b

        islemler = {
            Islem.TOPLA: operator.add,
            Islem.CIKAR: operator.sub,
            Islem.CARP: operator.mul,
            Islem.BOL: operator.truediv,
            Islem.US: operator.pow,
        }

        islem_fonksiyonu = islemler[islem]

        try:
            if islem == Islem.BOL and b == 0:
                raise ZeroDivisionError("Sıfıra bölme yapılamaz")

            sonuc = islem_fonksiyonu(a, b)

            if input_data.sonucu_yuvarla:
                sonuc = round(sonuc)

            yield "sonuc", sonuc

        except ZeroDivisionError:
            yield "sonuc", float("inf")  # Sıfıra bölme için sonsuz döndür
        except Exception:
            yield "sonuc", float("nan")  # Diğer hatalar için NaN döndür


class ElemanSayisiBlok(Block):
    class Girdi(BlockSchema):
        koleksiyon: Any = SchemaField(
            description="Saymak istediğiniz koleksiyonu girin. Bu bir liste, sözlük, string veya başka bir iterable olabilir.",
            placeholder="Örneğin: [1, 2, 3] veya {'a': 1, 'b': 2} veya 'merhaba'",
        )

    class Cikti(BlockSchema):
        sayi: int = SchemaField(description="Koleksiyondaki eleman sayısı")

    def __init__(self):
        super().__init__(
            id="3c9c2f42-b0c3-435f-ba35-05f7a25c772a",
            input_schema=ElemanSayisiBlok.Girdi,
            output_schema=ElemanSayisiBlok.Cikti,
            description="Bir koleksiyondaki eleman sayısını sayar.",
            categories={BlockCategory.LOGIC},
            test_input={"koleksiyon": [1, 2, 3, 4, 5]},
            test_output=[
                ("sayi", 5),
            ],
        )

    def run(self, input_data: Girdi, **kwargs) -> BlockOutput:
        koleksiyon = input_data.koleksiyon

        try:
            if isinstance(koleksiyon, (str, list, tuple, set, dict)):
                sayi = len(koleksiyon)
            elif hasattr(koleksiyon, "__iter__"):
                sayi = sum(1 for _ in koleksiyon)
            else:
                raise ValueError("Girdi sayılabilir bir koleksiyon değil")

            yield "sayi", sayi

        except Exception:
            yield "sayi", -1  # Hata durumunda -1 döndür
