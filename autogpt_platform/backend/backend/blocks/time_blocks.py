import time
from datetime import datetime, timedelta
from typing import Any, Union

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class GetCurrentTimeBlock(Block):
    class Input(BlockSchema):
        tetikleyici: str = SchemaField(
            description="Geçerli zamanı çıkarmak için herhangi bir veriyi tetikleyin"
        )
        format: str = SchemaField(
            description="Çıktı zamanı formatı", default="%H:%M:%S"
        )

    class Output(BlockSchema):
        zaman: str = SchemaField(
            description="Belirtilen formatta geçerli zaman (varsayılan: %H:%M:%S)"
        )

    def __init__(self):
        super().__init__(
            id="a892b8d9-3e4e-4e9c-9c1e-75f8efcf1bfa",
            description="Bu blok geçerli zamanı çıktılar.",
            categories={BlockCategory.TEXT},
            input_schema=GetCurrentTimeBlock.Input,
            output_schema=GetCurrentTimeBlock.Output,
            test_input=[
                {"tetikleyici": "Merhaba"},
                {"tetikleyici": "Merhaba", "format": "%H:%M"},
            ],
            test_output=[
                ("zaman", lambda _: time.strftime("%H:%M:%S")),
                ("zaman", lambda _: time.strftime("%H:%M")),
            ],
        )

    def run(self, input_data: Input, **kwargs) -> BlockOutput:
        current_time = time.strftime(input_data.format)
        yield "zaman", current_time


class GetCurrentDateBlock(Block):
    class Input(BlockSchema):
        tetikleyici: str = SchemaField(
            description="Geçerli tarihi çıkarmak için herhangi bir veriyi tetikleyin"
        )
        ofset: Union[int, str] = SchemaField(
            title="Gün Ofseti",
            description="Geçerli tarihten gün ofseti",
            default=0,
        )
        format: str = SchemaField(
            description="Çıktı tarihi formatı", default="%Y-%m-%d"
        )

    class Output(BlockSchema):
        tarih: str = SchemaField(
            description="Belirtilen formatta geçerli tarih (varsayılan: YYYY-MM-DD)"
        )

    def __init__(self):
        super().__init__(
            id="b29c1b50-5d0e-4d9f-8f9d-1b0e6fcbf0b1",
            description="Bu blok geçerli tarihi isteğe bağlı bir ofset ile çıktılar.",
            categories={BlockCategory.TEXT},
            input_schema=GetCurrentDateBlock.Input,
            output_schema=GetCurrentDateBlock.Output,
            test_input=[
                {"tetikleyici": "Merhaba", "ofset": "7"},
                {"tetikleyici": "Merhaba", "ofset": "7", "format": "%m/%d/%Y"},
            ],
            test_output=[
                (
                    "tarih",
                    lambda t: abs(datetime.now() - datetime.strptime(t, "%Y-%m-%d"))
                    < timedelta(days=8),  # 7 gün fark + 1 gün hata payı.
                ),
                (
                    "tarih",
                    lambda t: abs(datetime.now() - datetime.strptime(t, "%m/%d/%Y"))
                    < timedelta(days=8),
                    # 7 gün fark + 1 gün hata payı.
                ),
            ],
        )

    def run(self, input_data: Input, **kwargs) -> BlockOutput:
        try:
            ofset = int(input_data.ofset)
        except ValueError:
            ofset = 0
        current_date = datetime.now() - timedelta(days=ofset)
        yield "tarih", current_date.strftime(input_data.format)


class GetCurrentDateAndTimeBlock(Block):
    class Input(BlockSchema):
        tetikleyici: str = SchemaField(
            description="Geçerli tarih ve zamanı çıkarmak için herhangi bir veriyi tetikleyin"
        )
        format: str = SchemaField(
            description="Çıktı tarih ve zaman formatı",
            default="%Y-%m-%d %H:%M:%S",
        )

    class Output(BlockSchema):
        tarih_zaman: str = SchemaField(
            description="Belirtilen formatta geçerli tarih ve zaman (varsayılan: YYYY-MM-DD HH:MM:SS)"
        )

    def __init__(self):
        super().__init__(
            id="716a67b3-6760-42e7-86dc-18645c6e00fc",
            description="Bu blok geçerli tarih ve zamanı çıktılar.",
            categories={BlockCategory.TEXT},
            input_schema=GetCurrentDateAndTimeBlock.Input,
            output_schema=GetCurrentDateAndTimeBlock.Output,
            test_input=[
                {"tetikleyici": "Merhaba"},
            ],
            test_output=[
                (
                    "tarih_zaman",
                    lambda t: abs(
                        datetime.now() - datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    )
                    < timedelta(seconds=10),  # 10 saniye hata payı.
                ),
            ],
        )

    def run(self, input_data: Input, **kwargs) -> BlockOutput:
        current_date_time = time.strftime(input_data.format)
        yield "tarih_zaman", current_date_time


class CountdownTimerBlock(Block):
    class Input(BlockSchema):
        input_mesaj: Any = SchemaField(
            advanced=False,
            description="Zamanlayıcı bittikten sonra çıkacak mesaj",
            default="zamanlayıcı bitti",
        )
        saniye: Union[int, str] = SchemaField(
            advanced=False, description="Süre (saniye)", default=0
        )
        dakika: Union[int, str] = SchemaField(
            advanced=False, description="Süre (dakika)", default=0
        )
        saat: Union[int, str] = SchemaField(
            advanced=False, description="Süre (saat)", default=0
        )
        gün: Union[int, str] = SchemaField(
            advanced=False, description="Süre (gün)", default=0
        )

    class Output(BlockSchema):
        output_mesaj: Any = SchemaField(
            description="Zamanlayıcı bittikten sonra çıkacak mesaj"
        )

    def __init__(self):
        super().__init__(
            id="d67a9c52-5e4e-11e2-bcfd-0800200c9a71",
            description="Bu blok belirtilen süre sonra tetiklenir.",
            categories={BlockCategory.TEXT},
            input_schema=CountdownTimerBlock.Input,
            output_schema=CountdownTimerBlock.Output,
            test_input=[
                {"saniye": 1},
                {"input_mesaj": "Özel mesaj"},
            ],
            test_output=[
                ("output_mesaj", "zamanlayıcı bitti"),
                ("output_mesaj", "Özel mesaj"),
            ],
        )

    def run(self, input_data: Input, **kwargs) -> BlockOutput:
        saniye = int(input_data.saniye)
        dakika = int(input_data.dakika)
        saat = int(input_data.saat)
        gün = int(input_data.gün)

        toplam_saniye = saniye + dakika * 60 + saat * 3600 + gün * 86400

        time.sleep(toplam_saniye)
        yield "output_mesaj", input_data.input_mesaj
