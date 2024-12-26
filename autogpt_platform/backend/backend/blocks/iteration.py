from typing import Any

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField
from backend.util.json import json


class StepThroughItemsBlock(Block):
    class Input(BlockSchema):
        items: list = SchemaField(
            advanced=False,
            description="Üzerinde iterasyon yapılacak liste veya sözlük",
            placeholder="[1, 2, 3, 4, 5] veya {'anahtar1': 'değer1', 'anahtar2': 'değer2'}",
            default=[],
        )
        items_object: dict = SchemaField(
            advanced=False,
            description="Üzerinde iterasyon yapılacak liste veya sözlük",
            placeholder="[1, 2, 3, 4, 5] veya {'anahtar1': 'değer1', 'anahtar2': 'değer2'}",
            default={},
        )
        items_str: str = SchemaField(
            advanced=False,
            description="Üzerinde iterasyon yapılacak liste veya sözlük",
            placeholder="[1, 2, 3, 4, 5] veya {'anahtar1': 'değer1', 'anahtar2': 'değer2'}",
            default="",
        )

    class Output(BlockSchema):
        item: Any = SchemaField(description="Iterasyondaki mevcut öğe")
        key: Any = SchemaField(
            description="Iterasyondaki mevcut öğenin anahtarı veya indeksi",
        )

    def __init__(self):
        super().__init__(
            id="f66a3543-28d3-4ab5-8945-9b336371e2ce",
            input_schema=StepThroughItemsBlock.Input,
            output_schema=StepThroughItemsBlock.Output,
            categories={BlockCategory.LOGIC},
            description="Bir liste veya sözlük üzerinde iterasyon yapar ve her öğeyi çıktılar.",
            test_input={"items": [1, 2, 3, {"anahtar1": "değer1", "anahtar2": "değer2"}]},
            test_output=[
                ("item", 1),
                ("key", 0),
                ("item", 2),
                ("key", 1),
                ("item", 3),
                ("key", 2),
                ("item", {"anahtar1": "değer1", "anahtar2": "değer2"}),
                ("key", 3),
            ],
            test_mock={},
        )

    def run(self, input_data: Input, **kwargs) -> BlockOutput:
        for data in [input_data.items, input_data.items_object, input_data.items_str]:
            if not data:
                continue
            if isinstance(data, str):
                items = json.loads(data)
            else:
                items = data
            if isinstance(items, dict):
                # Eğer items bir sözlükse, değerleri üzerinde iterasyon yap
                for key, item in items.items():
                    yield "item", item
                    yield "key", key
            else:
                # Eğer items bir listeyse, liste üzerinde iterasyon yap
                for index, item in enumerate(items):
                    yield "item", item
                    yield "key", index
