import re

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class KodCikarmaBloku(Block):
    class Girdi(BlockSchema):
        metin: str = SchemaField(
            description="Kod bloklarını çıkarmak için metin (örneğin, AI yanıtı)",
            placeholder="Kod bloklarını içeren metni girin",
        )

    class Cikti(BlockSchema):
        html: str = SchemaField(description="Çıkarılan HTML kodu")
        css: str = SchemaField(description="Çıkarılan CSS kodu")
        javascript: str = SchemaField(description="Çıkarılan JavaScript kodu")
        python: str = SchemaField(description="Çıkarılan Python kodu")
        sql: str = SchemaField(description="Çıkarılan SQL kodu")
        java: str = SchemaField(description="Çıkarılan Java kodu")
        cpp: str = SchemaField(description="Çıkarılan C++ kodu")
        csharp: str = SchemaField(description="Çıkarılan C# kodu")
        json_kodu: str = SchemaField(description="Çıkarılan JSON kodu")
        bash: str = SchemaField(description="Çıkarılan Bash kodu")
        php: str = SchemaField(description="Çıkarılan PHP kodu")
        ruby: str = SchemaField(description="Çıkarılan Ruby kodu")
        yaml: str = SchemaField(description="Çıkarılan YAML kodu")
        markdown: str = SchemaField(description="Çıkarılan Markdown kodu")
        typescript: str = SchemaField(description="Çıkarılan TypeScript kodu")
        xml: str = SchemaField(description="Çıkarılan XML kodu")
        kalan_metin: str = SchemaField(
            description="Kod çıkarıldıktan sonra kalan metin"
        )

    def __init__(self):
        super().__init__(
            id="d3a7d896-3b78-4f44-8b4b-48fbf4f0bcd8",
            description="Metinden kod bloklarını çıkarır ve programlama dillerini tanımlar",
            categories={BlockCategory.TEXT},
            input_schema=KodCikarmaBloku.Girdi,
            output_schema=KodCikarmaBloku.Cikti,
            test_input={
                "metin": "İşte bir Python örneği:\n```python\nprint('Merhaba Dünya')\n```\nVe biraz HTML:\n```html\n<h1>Başlık</h1>\n```"
            },
            test_output=[
                ("html", "<h1>Başlık</h1>"),
                ("python", "print('Merhaba Dünya')"),
                ("kalan_metin", "İşte bir Python örneği:\nVe biraz HTML:"),
            ],
        )

    def calistir(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        # Desteklenen programlama dillerinin listesi ve eşlenmiş takma adları
        dil_takma_adlari = {
            "html": ["html", "htm"],
            "css": ["css"],
            "javascript": ["javascript", "js"],
            "python": ["python", "py"],
            "sql": ["sql"],
            "java": ["java"],
            "cpp": ["cpp", "c++"],
            "csharp": ["csharp", "c#", "cs"],
            "json_kodu": ["json"],
            "bash": ["bash", "shell", "sh"],
            "php": ["php"],
            "ruby": ["ruby", "rb"],
            "yaml": ["yaml", "yml"],
            "markdown": ["markdown", "md"],
            "typescript": ["typescript", "ts"],
            "xml": ["xml"],
        }

        # Her dil için kodu çıkar
        for kanonik_ad, takma_adlar in dil_takma_adlari.items():
            kod = ""
            # Dil için her takma adı dene
            for takma_ad in takma_adlar:
                takma_ad_icin_kod = self.kod_cikar(girdi_verisi.metin, takma_ad)
                if takma_ad_icin_kod:
                    kod = kod + "\n\n" + takma_ad_icin_kod if kod else takma_ad_icin_kod

            if kod:  # Sadece gerçek kod içeriği varsa çıktı ver
                yield kanonik_ad, kod

        # Metinden tüm kod bloklarını çıkararak kalan metni al
        desen = (
            r"```(?:"
            + "|".join(
                re.escape(takma_ad)
                for takma_adlar in dil_takma_adlari.values()
                for takma_ad in takma_adlar
            )
            + r")\s+[\s\S]*?```"
        )

        kalan_metin = re.sub(desen, "", girdi_verisi.metin).strip()
        kalan_metin = re.sub(r"\n\s*\n", "\n", kalan_metin)

        if kalan_metin:  # Sadece kalan metin varsa çıktı ver
            yield "kalan_metin", kalan_metin

    def kod_cikar(self, metin: str, dil: str) -> str:
        # Dil stringindeki özel regex karakterlerini kaçış karakteri ile işaretle
        dil = re.escape(dil)
        # ```dil``` blokları içinde yer alan tüm kod bloklarını çıkar
        desen = re.compile(rf"```{dil}\s+(.*?)```", re.DOTALL | re.IGNORECASE)
        eslesmeler = desen.finditer(metin)
        # Bu dil için tüm kod bloklarını yeni satırlar ile birleştir
        kod_bloklari = [eslesme.group(1).strip() for eslesme in eslesmeler]
        return "\n\n".join(kod_bloklari) if kod_bloklari else ""
