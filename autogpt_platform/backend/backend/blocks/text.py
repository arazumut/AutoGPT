import re
from typing import Any

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField
from backend.util import json, text

formatter = text.TextFormatter()


class MetinDeseniEşleştirmeBloğu(Block):
    class Girdi(BlockSchema):
        metin: Any = SchemaField(description="Eşleştirilecek metin")
        desen: str = SchemaField(description="Eşleştirilecek desen (Regex)")
        veri: Any = SchemaField(description="Çıktıya iletilecek veri")
        büyük_küçük_harf_duyarlı: bool = SchemaField(
            description="Büyük/küçük harf duyarlı eşleştirme", default=True
        )
        nokta_herşeyi_eşleştirir: bool = SchemaField(description="Nokta her şeyi eşleştirir", default=True)

    class Çıktı(BlockSchema):
        olumlu: Any = SchemaField(description="Eşleşme bulunursa çıktı verisi")
        olumsuz: Any = SchemaField(description="Eşleşme bulunmazsa çıktı verisi")

    def __init__(self):
        super().__init__(
            id="3060088f-6ed9-4928-9ba7-9c92823a7ccd",
            description="Metni bir regex deseniyle eşleştirir ve eşleşmeye göre veriyi olumlu veya olumsuz çıktıya iletir.",
            categories={BlockCategory.TEXT},
            input_schema=MetinDeseniEşleştirmeBloğu.Girdi,
            output_schema=MetinDeseniEşleştirmeBloğu.Çıktı,
            test_input=[
                {"metin": "ABC", "desen": "ab", "veri": "X", "büyük_küçük_harf_duyarlı": False},
                {"metin": "ABC", "desen": "ab", "veri": "Y", "büyük_küçük_harf_duyarlı": True},
                {"metin": "Hello World!", "desen": ".orld.+", "veri": "Z"},
                {"metin": "Hello World!", "desen": "World![a-z]+", "veri": "Z"},
            ],
            test_output=[
                ("olumlu", "X"),
                ("olumsuz", "Y"),
                ("olumlu", "Z"),
                ("olumsuz", "Z"),
            ],
        )

    def run(self, input_data: Girdi, **kwargs) -> BlockOutput:
        output = input_data.veri or input_data.metin
        flags = 0
        if not input_data.büyük_küçük_harf_duyarlı:
            flags = flags | re.IGNORECASE
        if input_data.nokta_herşeyi_eşleştirir:
            flags = flags | re.DOTALL

        if isinstance(input_data.metin, str):
            metin = input_data.metin
        else:
            metin = json.dumps(input_data.metin)

        if re.search(input_data.desen, metin, flags=flags):
            yield "olumlu", output
        else:
            yield "olumsuz", output


class MetinBilgisiÇıkarmaBloğu(Block):
    class Girdi(BlockSchema):
        metin: Any = SchemaField(description="Parçalanacak metin")
        desen: str = SchemaField(description="Parçalanacak desen (Regex)")
        grup: int = SchemaField(description="Çıkarılacak grup numarası", default=0)
        büyük_küçük_harf_duyarlı: bool = SchemaField(
            description="Büyük/küçük harf duyarlı eşleştirme", default=True
        )
        nokta_herşeyi_eşleştirir: bool = SchemaField(description="Nokta her şeyi eşleştirir", default=True)
        tümünü_bul: bool = SchemaField(description="Tüm eşleşmeleri bul", default=False)

    class Çıktı(BlockSchema):
        olumlu: str = SchemaField(description="Çıkarılan metin")
        olumsuz: str = SchemaField(description="Orijinal metin")

    def __init__(self):
        super().__init__(
            id="3146e4fe-2cdd-4f29-bd12-0c9d5bb4deb0",
            description="Bu blok, verilen metinden deseni (regex) kullanarak metin çıkarır.",
            categories={BlockCategory.TEXT},
            input_schema=MetinBilgisiÇıkarmaBloğu.Girdi,
            output_schema=MetinBilgisiÇıkarmaBloğu.Çıktı,
            test_input=[
                {"metin": "Hello, World!", "desen": "Hello, (.+)", "grup": 1},
                {"metin": "Hello, World!", "desen": "Hello, (.+)", "grup": 0},
                {"metin": "Hello, World!", "desen": "Hello, (.+)", "grup": 2},
                {"metin": "Hello, World!", "desen": "hello,", "büyük_küçük_harf_duyarlı": False},
                {
                    "metin": "Hello, World!! Hello, Earth!!",
                    "desen": "Hello, (\\S+)",
                    "grup": 1,
                    "tümünü_bul": False,
                },
                {
                    "metin": "Hello, World!! Hello, Earth!!",
                    "desen": "Hello, (\\S+)",
                    "grup": 1,
                    "tümünü_bul": True,
                },
            ],
            test_output=[
                ("olumlu", "World!"),
                ("olumlu", "Hello, World!"),
                ("olumsuz", "Hello, World!"),
                ("olumlu", "Hello,"),
                ("olumlu", "World!!"),
                ("olumlu", "World!!"),
                ("olumlu", "Earth!!"),
            ],
        )

    def run(self, input_data: Girdi, **kwargs) -> BlockOutput:
        flags = 0
        if not input_data.büyük_küçük_harf_duyarlı:
            flags = flags | re.IGNORECASE
        if input_data.nokta_herşeyi_eşleştirir:
            flags = flags | re.DOTALL

        if isinstance(input_data.metin, str):
            txt = input_data.metin
        else:
            txt = json.dumps(input_data.metin)

        matches = [
            match.group(input_data.grup)
            for match in re.finditer(input_data.desen, txt, flags)
            if input_data.grup <= len(match.groups())
        ]
        for match in matches:
            yield "olumlu", match
            if not input_data.tümünü_bul:
                return
        if not matches:
            yield "olumsuz", input_data.metin


class MetinŞablonuDoldurmaBloğu(Block):
    class Girdi(BlockSchema):
        değerler: dict[str, Any] = SchemaField(
            description="Formatta kullanılacak değerler (dict)"
        )
        format: str = SchemaField(
            description="`değerler` kullanılarak metni formatlamak için şablon"
        )

    class Çıktı(BlockSchema):
        çıktı: str = SchemaField(description="Formatlanmış metin")

    def __init__(self):
        super().__init__(
            id="db7d8f02-2f44-4c55-ab7a-eae0941f0c30",
            description="Bu blok, verilen metinleri format şablonunu kullanarak formatlar.",
            categories={BlockCategory.TEXT},
            input_schema=MetinŞablonuDoldurmaBloğu.Girdi,
            output_schema=MetinŞablonuDoldurmaBloğu.Çıktı,
            test_input=[
                {
                    "değerler": {"isim": "Alice", "merhaba": "Hello", "dünya": "World!"},
                    "format": "{merhaba}, {dünya} {{isim}}",
                },
                {
                    "değerler": {"liste": ["Hello", " World!"]},
                    "format": "{% for item in liste %}{{ item }}{% endfor %}",
                },
                {
                    "değerler": {},
                    "format": "{% set isim = 'Alice' %}Hello, World! {{ isim }}",
                },
            ],
            test_output=[
                ("çıktı", "Hello, World! Alice"),
                ("çıktı", "Hello World!"),
                ("çıktı", "Hello, World! Alice"),
            ],
        )

    def run(self, input_data: Girdi, **kwargs) -> BlockOutput:
        yield "çıktı", formatter.format_string(input_data.format, input_data.değerler)


class MetinleriBirleştirmeBloğu(Block):
    class Girdi(BlockSchema):
        girdi: list[str] = SchemaField(description="Birleştirilecek metin girişi")
        ayırıcı: str = SchemaField(
            description="Metinleri birleştirmek için ayırıcı", default=""
        )

    class Çıktı(BlockSchema):
        çıktı: str = SchemaField(description="Birleştirilmiş metin")

    def __init__(self):
        super().__init__(
            id="e30a4d42-7b7d-4e6a-b36e-1f9b8e3b7d85",
            description="Bu blok, birden fazla metin girişini tek bir çıktı metnine birleştirir.",
            categories={BlockCategory.TEXT},
            input_schema=MetinleriBirleştirmeBloğu.Girdi,
            output_schema=MetinleriBirleştirmeBloğu.Çıktı,
            test_input=[
                {"girdi": ["Hello world I like ", "cake and to go for walks"]},
                {"girdi": ["This is a test", "Hi!"], "ayırıcı": "! "},
            ],
            test_output=[
                ("çıktı", "Hello world I like cake and to go for walks"),
                ("çıktı", "This is a test! Hi!"),
            ],
        )

    def run(self, input_data: Girdi, **kwargs) -> BlockOutput:
        birleştirilmiş_metin = input_data.ayırıcı.join(input_data.girdi)
        yield "çıktı", birleştirilmiş_metin
