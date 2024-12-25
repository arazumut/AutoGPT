from backend.data.block import BlockOutput, BlockSchema
from backend.data.model import APIKeyCredentials, SchemaField

from ._api import (
    TEST_CREDENTIALS,
    TEST_CREDENTIALS_INPUT,
    Slant3DCredentialsField,
    Slant3DCredentialsInput,
)
from .base import Slant3DBlockBase


class Slant3DSlicerBlock(Slant3DBlockBase):
    """3D model dosyalarını dilimlemek için blok"""

    class Input(BlockSchema):
        credentials: Slant3DCredentialsInput = Slant3DCredentialsField()
        file_url: str = SchemaField(
            description="Dilimlenecek 3D model dosyasının URL'si (STL)"
        )

    class Output(BlockSchema):
        message: str = SchemaField(description="Yanıt mesajı")
        price: float = SchemaField(description="Baskı için hesaplanan fiyat")
        error: str = SchemaField(description="Dilimleme başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="f8a12c8d-3e4b-4d5f-b6a7-8c9d0e1f2g3h",
            description="Bir 3D model dosyasını dilimleyin ve fiyat bilgisi alın",
            input_schema=self.Input,
            output_schema=self.Output,
            test_input={
                "credentials": TEST_CREDENTIALS_INPUT,
                "file_url": "https://example.com/model.stl",
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=[("message", "Dilimleme başarılı"), ("price", 8.23)],
            test_mock={
                "_make_request": lambda *args, **kwargs: {
                    "message": "Dilimleme başarılı",
                    "data": {"price": 8.23},
                }
            },
        )

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        try:
            result = self._make_request(
                "POST",
                "slicer",
                credentials.api_key.get_secret_value(),
                json={"fileURL": input_data.file_url},
            )
            yield "message", result["message"]
            yield "price", result["data"]["price"]
        except Exception as e:
            yield "error", str(e)
            raise
