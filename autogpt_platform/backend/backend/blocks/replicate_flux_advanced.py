import os
from enum import Enum
from typing import Literal

import replicate
from pydantic import SecretStr
from replicate.helpers import FileOutput

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
)
from backend.integrations.providers import ProviderName

# Test kimlik bilgileri
TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="replicate",
    api_key=SecretStr("mock-replicate-api-key"),
    title="Mock Replicate API key",
    expires_at=None,
)
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.type,
}

# Model adı enum
class ReplicateFluxModelName(str, Enum):
    FLUX_SCHNELL = "Flux Schnell"
    FLUX_PRO = "Flux Pro"
    FLUX_PRO1_1 = "Flux Pro 1.1"

    @property
    def api_name(self):
        api_names = {
            ReplicateFluxModelName.FLUX_SCHNELL: "black-forest-labs/flux-schnell",
            ReplicateFluxModelName.FLUX_PRO: "black-forest-labs/flux-pro",
            ReplicateFluxModelName.FLUX_PRO1_1: "black-forest-labs/flux-1.1-pro",
        }
        return api_names[self]

# Görüntü türü enum
class ImageType(str, Enum):
    WEBP = "webp"
    JPG = "jpg"
    PNG = "png"

class ReplicateFluxAdvancedModelBlock(Block):
    class Input(BlockSchema):
        credentials: CredentialsMetaInput[
            Literal[ProviderName.REPLICATE], Literal["api_key"]
        ] = CredentialsField(
            description="Replicate entegrasyonu, üzerinde kullanıldığı bloklar için yeterli izinlere sahip herhangi bir API anahtarı ile kullanılabilir.",
        )
        prompt: str = SchemaField(
            description="Görüntü oluşturma için metin istemi",
            placeholder="örneğin, 'Gün batımında fütüristik bir şehir manzarası'",
            title="İstem",
        )
        replicate_model_name: ReplicateFluxModelName = SchemaField(
            description="Görüntü Oluşturma Modelinin adı, örneğin Flux Schnell",
            default=ReplicateFluxModelName.FLUX_SCHNELL,
            title="Görüntü Oluşturma Modeli",
            advanced=False,
        )
        seed: int | None = SchemaField(
            description="Rastgele tohum. Tekrar üretilebilir oluşturma için ayarlayın",
            default=None,
            title="Tohum",
        )
        steps: int = SchemaField(
            description="Difüzyon adımlarının sayısı",
            default=25,
            title="Adımlar",
        )
        guidance: float = SchemaField(
            description=(
                "Metin istemine uyum ile görüntü kalitesi/çeşitliliği arasındaki dengeyi kontrol eder. "
                "Daha yüksek değerler, çıktının isteme daha sıkı uymasını sağlar ancak genel görüntü kalitesini düşürebilir."
            ),
            default=3,
            title="Rehberlik",
        )
        interval: float = SchemaField(
            description=(
                "Aralık, olası çıktılardaki varyansı artıran bir ayardır. "
                "Bu değeri düşük ayarlamak, daha tutarlı çıktılarla güçlü istem takibini sağlar."
            ),
            default=2,
            title="Aralık",
        )
        aspect_ratio: str = SchemaField(
            description="Oluşturulan görüntünün en boy oranı",
            default="1:1",
            title="En Boy Oranı",
            placeholder="Seçenekler: 1:1, 16:9, 2:3, 3:2, 4:5, 5:4, 9:16",
        )
        output_format: ImageType = SchemaField(
            description="Çıktı görüntüsünün dosya formatı",
            default=ImageType.WEBP,
            title="Çıktı Formatı",
        )
        output_quality: int = SchemaField(
            description=(
                "Çıktı görüntülerini kaydederken kalite, 0'dan 100'e kadar. "
                ".png çıktıları için geçerli değildir"
            ),
            default=80,
            title="Çıktı Kalitesi",
        )
        safety_tolerance: int = SchemaField(
            description="Güvenlik toleransı, 1 en katı ve 5 en hoşgörülü",
            default=2,
            title="Güvenlik Toleransı",
        )

    class Output(BlockSchema):
        result: str = SchemaField(description="Oluşturulan çıktı")
        error: str = SchemaField(description="Model çalıştırma başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="90f8c45e-e983-4644-aa0b-b4ebe2f531bc",
            description="Bu blok, Replicate üzerinde gelişmiş ayarlarla Flux modellerini çalıştırır.",
            categories={BlockCategory.AI},
            input_schema=ReplicateFluxAdvancedModelBlock.Input,
            output_schema=ReplicateFluxAdvancedModelBlock.Output,
            test_input={
                "credentials": TEST_CREDENTIALS_INPUT,
                "replicate_model_name": ReplicateFluxModelName.FLUX_SCHNELL,
                "prompt": "Gün doğumunda sakin bir gölün güzel bir manzara resmi",
                "seed": None,
                "steps": 25,
                "guidance": 3.0,
                "interval": 2.0,
                "aspect_ratio": "1:1",
                "output_format": ImageType.PNG,
                "output_quality": 80,
                "safety_tolerance": 2,
            },
            test_output=[
                (
                    "result",
                    "https://replicate.com/output/generated-image-url.jpg",
                ),
            ],
            test_mock={
                "run_model": lambda api_key, model_name, prompt, seed, steps, guidance, interval, aspect_ratio, output_format, output_quality, safety_tolerance: "https://replicate.com/output/generated-image-url.jpg",
            },
            test_credentials=TEST_CREDENTIALS,
        )

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        # Tohum sağlanmadıysa, rastgele bir tohum oluştur
        seed = input_data.seed
        if seed is None:
            seed = int.from_bytes(os.urandom(4), "big")

        # Sağlanan girdilerle modeli çalıştır
        result = self.run_model(
            api_key=credentials.api_key,
            model_name=input_data.replicate_model_name.api_name,
            prompt=input_data.prompt,
            seed=seed,
            steps=input_data.steps,
            guidance=input_data.guidance,
            interval=input_data.interval,
            aspect_ratio=input_data.aspect_ratio,
            output_format=input_data.output_format,
            output_quality=input_data.output_quality,
            safety_tolerance=input_data.safety_tolerance,
        )
        yield "result", result

    def run_model(
        self,
        api_key: SecretStr,
        model_name,
        prompt,
        seed,
        steps,
        guidance,
        interval,
        aspect_ratio,
        output_format,
        output_quality,
        safety_tolerance,
    ):
        # Replicate istemcisini API anahtarı ile başlat
        client = replicate.Client(api_token=api_key.get_secret_value())

        # Ek parametrelerle modeli çalıştır
        output: FileOutput | list[FileOutput] = client.run(
            f"{model_name}",
            input={
                "prompt": prompt,
                "seed": seed,
                "steps": steps,
                "guidance": guidance,
                "interval": interval,
                "aspect_ratio": aspect_ratio,
                "output_format": output_format,
                "output_quality": output_quality,
                "safety_tolerance": safety_tolerance,
            },
            wait=False,
        )

        # Çıktının bir liste mi yoksa bir string mi olduğunu kontrol et ve buna göre çıkar; aksi takdirde varsayılan bir mesaj ata
        if isinstance(output, list) and len(output) > 0:
            if isinstance(output[0], FileOutput):
                result_url = output[0].url  # Çıktı bir listeyse, ilk öğeyi al
            else:
                result_url = output[0]  # Çıktı bir liste ve FileOutput değilse, ilk öğeyi al. Asla olmamalı, ama her ihtimale karşı.
        elif isinstance(output, FileOutput):
            result_url = output.url  # Çıktı bir FileOutput ise, url'yi kullan
        elif isinstance(output, str):
            result_url = output  # Çıktı bir string ise (bazı nedenlerden dolayı janky type hinting nedeniyle), doğrudan kullan
        else:
            result_url = "Çıktı alınamadı"  # Çıktı beklenildiği gibi değilse, geri dönüş mesajı

        return result_url
