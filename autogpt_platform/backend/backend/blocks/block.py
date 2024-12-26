import os
import re
from typing import Type

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField


class BlockSetup(Block):
    """
    Bu blok, sistemdeki diğer blokların doğrulanmasını ve kurulmasını sağlar.

    NOT:
        Bu blok, sunucuda uzaktan kod yürütülmesine izin verir ve yalnızca geliştirme amaçlı kullanılmalıdır.
    """

    class Input(BlockSchema):
        code: str = SchemaField(
            description="Kurulacak bloğun Python kodu",
        )

    class Output(BlockSchema):
        success: str = SchemaField(
            description="Blok başarıyla kurulduğunda başarı mesajı",
        )
        error: str = SchemaField(
            description="Blok kurulumu başarısız olursa hata mesajı",
        )

    def __init__(self):
        super().__init__(
            id="45e78db5-03e9-447f-9395-308d712f5f08",
            description="Bir kod dizesi verildiğinde, bu blok bir blok kodunun sisteme doğrulanmasını ve kurulmasını sağlar.",
            categories={BlockCategory.BASIC},
            input_schema=BlockSetup.Input,
            output_schema=BlockSetup.Output,
            disabled=True,
        )

    def run(self, input_data: Input, **kwargs) -> BlockOutput:
        code = input_data.code

        if match := re.search(r"class (\w+)\(Block\):", code):
            class_name = match.group(1)
        else:
            raise RuntimeError("Kodda sınıf bulunamadı.")

        if match := re.search(r"id=\"(\w+-\w+-\w+-\w+-\w+)\"", code):
            file_name = match.group(1)
        else:
            raise RuntimeError("Kodda UUID bulunamadı.")

        block_directory = os.path.dirname(__file__)
        file_path = f"{block_directory}/{file_name}.py"
        module_name = f"backend.blocks.{file_name}"
        with open(file_path, "w") as f:
            f.write(code)

        try:
            module = __import__(module_name, fromlist=[class_name])
            block_class: Type[Block] = getattr(module, class_name)
            block = block_class()

            from backend.util.test import execute_block_test

            execute_block_test(block)
            yield "success", "Blok başarıyla kuruldu."
        except Exception as e:
            os.remove(file_path)
            raise RuntimeError(f"[Kod]\n{code}\n\n[Hata]\n{str(e)}")
