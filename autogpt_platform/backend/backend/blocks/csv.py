from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import ContributorDetails, SchemaField


class CsvOkumaBloğu(Block):
    class Girdi(BlockSchema):
        içerik: str = SchemaField(
            description="Okunacak CSV dosyasının içeriği",
            placeholder="a, b, c\n1,2,3\n4,5,6",
        )
        ayraç: str = SchemaField(
            description="CSV dosyasında kullanılan ayraç",
            default=",",
        )
        alıntı_karakteri: str = SchemaField(
            description="Alanları alıntılamak için kullanılan karakter",
            default='"',
        )
        kaçış_karakteri: str = SchemaField(
            description="Ayraç karakterini kaçırmak için kullanılan karakter",
            default="\\",
        )
        başlık_var_mı: bool = SchemaField(
            description="CSV dosyasının başlık satırı olup olmadığı",
            default=True,
        )
        atlanacak_satırlar: int = SchemaField(
            description="Dosyanın başından itibaren atlanacak satır sayısı",
            default=0,
        )
        boşlukları_sil: bool = SchemaField(
            description="Değerlerden boşlukları silip silmeyeceği",
            default=True,
        )
        atlanacak_sütunlar: list[str] = SchemaField(
            description="Satırın başından itibaren atlanacak sütunlar",
            default=[],
        )

    class Çıktı(BlockSchema):
        satır: dict[str, str] = SchemaField(
            description="CSV dosyasındaki her satırdan üretilen veri"
        )
        tüm_veri: list[dict[str, str]] = SchemaField(
            description="CSV dosyasındaki tüm veriler, satırların listesi olarak"
        )

    def __init__(self):
        super().__init__(
            id="acf7625e-d2cb-4941-bfeb-2819fc6fc015",
            input_schema=CsvOkumaBloğu.Girdi,
            output_schema=CsvOkumaBloğu.Çıktı,
            description="Bir CSV dosyasını okur ve verileri satırların listesi ve bireysel satırlar olarak çıktı verir.",
            contributors=[ContributorDetails(name="Nicholas Tindle")],
            categories={BlockCategory.TEXT, BlockCategory.DATA},
            test_input={
                "içerik": "a, b, c\n1,2,3\n4,5,6",
            },
            test_output=[
                ("satır", {"a": "1", "b": "2", "c": "3"}),
                ("satır", {"a": "4", "b": "5", "c": "6"}),
                (
                    "tüm_veri",
                    [
                        {"a": "1", "b": "2", "c": "3"},
                        {"a": "4", "b": "5", "c": "6"},
                    ],
                ),
            ],
        )

    def çalıştır(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        import csv
        from io import StringIO

        csv_dosyası = StringIO(girdi_verisi.içerik)
        okuyucu = csv.reader(
            csv_dosyası,
            delimiter=girdi_verisi.ayraç,
            quotechar=girdi_verisi.alıntı_karakteri,
            escapechar=girdi_verisi.kaçış_karakteri,
        )

        başlık = None
        if girdi_verisi.başlık_var_mı:
            başlık = next(okuyucu)
            if girdi_verisi.boşlukları_sil:
                başlık = [h.strip() for h in başlık]

        for _ in range(girdi_verisi.atlanacak_satırlar):
            next(okuyucu)

        def satırı_işle(satır):
            veri = {}
            for i, değer in enumerate(satır):
                if i not in girdi_verisi.atlanacak_sütunlar:
                    if girdi_verisi.başlık_var_mı and başlık:
                        veri[başlık[i]] = değer.strip() if girdi_verisi.boşlukları_sil else değer
                    else:
                        veri[str(i)] = değer.strip() if girdi_verisi.boşlukları_sil else değer
            return veri

        tüm_veri = []
        for satır in okuyucu:
            işlenmiş_satır = satırı_işle(satır)
            tüm_veri.append(işlenmiş_satır)
            yield "satır", işlenmiş_satır

        yield "tüm_veri", tüm_veri
