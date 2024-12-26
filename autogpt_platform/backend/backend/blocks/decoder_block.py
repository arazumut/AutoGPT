import codecs

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class MetinCozucuBlok(Block):
    class Girdi(BlockSchema):
        metin: str = SchemaField(
            description="Çözülecek kaçış karakterleri içeren bir metin",
            placeholder='\\n ve \\" kaçış karakterleri içeren tüm metin bloğunuz',
        )

    class Cikti(BlockSchema):
        cozulen_metin: str = SchemaField(
            description="Kaçış dizileri işlenmiş çözülen metin"
        )

    def __init__(self):
        super().__init__(
            id="2570e8fe-8447-43ed-84c7-70d657923231",
            description="Kaçış dizileri içeren bir metni gerçek metne çözer",
            categories={BlockCategory.TEXT},
            input_schema=MetinCozucuBlok.Girdi,
            output_schema=MetinCozucuBlok.Cikti,
            test_input={"metin": """Merhaba\nDünya!\nBu bir \"alıntılanmış\" metindir."""},
            test_output=[
                (
                    "cozulen_metin",
                    """Merhaba
Dünya!
Bu bir "alıntılanmış" metindir.""",
                )
            ],
        )

    def calistir(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        cozulen_metin = codecs.decode(girdi_verisi.metin, "unicode_escape")
        yield "cozulen_metin", cozulen_metin
