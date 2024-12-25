import os
import re
from typing import Type

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class BlokKurulumBloğu(Block):
    """
    Bu blok, sistemdeki diğer blokların doğrulanmasını ve kurulmasını sağlar.

    NOT:
        Bu blok, sunucuda uzaktan kod yürütülmesine izin verir ve yalnızca geliştirme amaçlı kullanılmalıdır.
    """

    class Girdi(BlockSchema):
        kod: str = SchemaField(
            description="Kurulacak bloğun Python kodu",
        )

    class Çıktı(BlockSchema):
        başarı: str = SchemaField(
            description="Blok başarıyla kurulduğunda başarı mesajı",
        )
        hata: str = SchemaField(
            description="Blok kurulumu başarısız olursa hata mesajı",
        )

    def __init__(self):
        super().__init__(
            id="45e78db5-03e9-447f-9395-308d712f5f08",
            description="Bir kod dizesi verildiğinde, bu blok bir blok kodunun sisteme doğrulanmasını ve kurulmasını sağlar.",
            categories={BlockCategory.BASIC},
            input_schema=BlokKurulumBloğu.Girdi,
            output_schema=BlokKurulumBloğu.Çıktı,
            disabled=True,
        )

    def çalıştır(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        kod = girdi_verisi.kod

        if arama := re.search(r"class (\w+)\(Block\):", kod):
            sınıf_adı = arama.group(1)
        else:
            raise RuntimeError("Kodda sınıf bulunamadı.")

        if arama := re.search(r"id=\"(\w+-\w+-\w+-\w+-\w+)\"", kod):
            dosya_adı = arama.group(1)
        else:
            raise RuntimeError("Kodda UUID bulunamadı.")

        blok_dizini = os.path.dirname(__file__)
        dosya_yolu = f"{blok_dizini}/{dosya_adı}.py"
        modül_adı = f"backend.blocks.{dosya_adı}"
        with open(dosya_yolu, "w") as f:
            f.write(kod)

        try:
            modül = __import__(modül_adı, fromlist=[sınıf_adı])
            blok_sınıfı: Type[Block] = getattr(modül, sınıf_adı)
            blok = blok_sınıfı()

            from backend.util.test import execute_block_test

            execute_block_test(blok)
            yield "başarı", "Blok başarıyla kuruldu."
        except Exception as e:
            os.remove(dosya_yolu)
            raise RuntimeError(f"[Kod]\n{kod}\n\n[Hata]\n{str(e)}")
