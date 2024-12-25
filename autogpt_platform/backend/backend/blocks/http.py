import json
from enum import Enum
from typing import Any

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField
from backend.util.request import requests


class HttpMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class WebIsteğiGonderBlok(Block):
    class Girdi(BlockSchema):
        url: str = SchemaField(
            description="İsteğin gönderileceği URL",
            placeholder="https://api.ornek.com",
        )
        method: HttpMethod = SchemaField(
            description="İstek için kullanılacak HTTP yöntemi",
            default=HttpMethod.POST,
        )
        headers: dict[str, str] = SchemaField(
            description="İstekle birlikte gönderilecek başlıklar",
            default={},
        )
        json_format: bool = SchemaField(
            title="JSON formatı",
            description="Gövdenin JSON formatında gönderilip alınacağı",
            default=True,
        )
        body: Any = SchemaField(
            description="İsteğin gövdesi",
            default=None,
        )

    class Çıktı(BlockSchema):
        response: object = SchemaField(description="Sunucudan gelen yanıt")
        client_error: object = SchemaField(description="4xx durum kodlarında hata")
        server_error: object = SchemaField(description="5xx durum kodlarında hata")

    def __init__(self):
        super().__init__(
            id="6595ae1f-b924-42cb-9a41-551a0611c4b4",
            description="Bu blok belirtilen URL'ye bir HTTP isteği yapar.",
            categories={BlockCategory.OUTPUT},
            input_schema=WebIsteğiGonderBlok.Girdi,
            output_schema=WebIsteğiGonderBlok.Çıktı,
        )

    def çalıştır(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        if isinstance(girdi_verisi.body, str):
            girdi_verisi.body = json.loads(girdi_verisi.body)

        response = requests.request(
            girdi_verisi.method.value,
            girdi_verisi.url,
            headers=girdi_verisi.headers,
            json=girdi_verisi.body if girdi_verisi.json_format else None,
            data=girdi_verisi.body if not girdi_verisi.json_format else None,
        )
        result = response.json() if girdi_verisi.json_format else response.text

        if response.status_code // 100 == 2:
            yield "response", result
        elif response.status_code // 100 == 4:
            yield "client_error", result
        elif response.status_code // 100 == 5:
            yield "server_error", result
        else:
            raise ValueError(f"Beklenmedik durum kodu: {response.status_code}")
