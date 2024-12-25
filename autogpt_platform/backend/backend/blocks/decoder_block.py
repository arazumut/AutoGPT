import codecs

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class MetinÇözücüBlok(Block):
    class Girdi(BlockSchema):
        metin: str = SchemaField(
            description="Çözülecek kaçış karakterleri içeren bir dize",
            placeholder='\\n ve \\" kaçış karakterleri içeren tüm metin bloğunuz',
        )

    class Çıktı(BlockSchema):
        çözülen_metin: str = SchemaField(
            description="Kaçış dizileri işlenmiş çözülen metin"
        )

    def __init__(self):
        super().__init__(
            id="2570e8fe-8447-43ed-84c7-70d657923231",
            description="Kaçış dizileri içeren bir dizeyi gerçek metne çözer",
            categories={BlockCategory.TEXT},
            input_schema=MetinÇözücüBlok.Girdi,
            output_schema=MetinÇözücüBlok.Çıktı,
            test_input={"metin": """Merhaba\nDünya!\nBu bir \"alıntılanmış\" dizedir."""},
            test_output=[
                (
                    "çözülen_metin",
                    """Merhaba
Dünya!
Bu bir "alıntılanmış" dizedir.""",
                )
            ],
        )

    def çalıştır(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        çözülen_metin = codecs.decode(girdi_verisi.metin, "unicode_escape")
        yield "çözülen_metin", çözülen_metin
