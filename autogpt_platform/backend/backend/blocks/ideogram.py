from enum import Enum
from typing import Any, Dict, Literal, Optional

from pydantic import SecretStr
from requests.exceptions import RequestException

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
)
from backend.integrations.providers import ProviderName
from backend.util.request import requests

TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="ideogram",
    api_key=SecretStr("mock-ideogram-api-key"),
    title="Mock Ideogram API key",
    expires_at=None,
)
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.type,
}


class IdeogramModelName(str, Enum):
    V2 = "V_2"
    V1 = "V_1"
    V1_TURBO = "V_1_TURBO"
    V2_TURBO = "V_2_TURBO"


class MagicPromptOption(str, Enum):
    OTOMATIK = "OTOMATIK"
    ACIK = "ACIK"
    KAPALI = "KAPALI"


class StyleType(str, Enum):
    OTOMATIK = "OTOMATIK"
    GENEL = "GENEL"
    GERCEKCI = "GERCEKCI"
    TASARIM = "TASARIM"
    RENDER_3D = "RENDER_3D"
    ANIME = "ANIME"


class ColorPalettePreset(str, Enum):
    YOK = "YOK"
    KOR = "KOR"
    TAZE = "TAZE"
    ORMAN = "ORMAN"
    SIHIR = "SIHIR"
    KARPUZ = "KARPUZ"
    MOZAIK = "MOZAIK"
    PASTEL = "PASTEL"
    ULTRAMARIN = "ULTRAMARIN"


class AspectRatio(str, Enum):
    ORAN_10_16 = "ORAN_10_16"
    ORAN_16_10 = "ORAN_16_10"
    ORAN_9_16 = "ORAN_9_16"
    ORAN_16_9 = "ORAN_16_9"
    ORAN_3_2 = "ORAN_3_2"
    ORAN_2_3 = "ORAN_2_3"
    ORAN_4_3 = "ORAN_4_3"
    ORAN_3_4 = "ORAN_3_4"
    ORAN_1_1 = "ORAN_1_1"
    ORAN_1_3 = "ORAN_1_3"
    ORAN_3_1 = "ORAN_3_1"


class UpscaleOption(str, Enum):
    AI_YUKSELTME = "AI Yükseltme"
    YUKSELTME_YOK = "Yükseltme Yok"


class IdeogramModelBlock(Block):
    class Input(BlockSchema):
        credentials: CredentialsMetaInput[
            Literal[ProviderName.IDEOGRAM], Literal["api_key"]
        ] = CredentialsField(
            description="Ideogram entegrasyonu, yeterli izinlere sahip herhangi bir API anahtarı ile kullanılabilir.",
        )
        prompt: str = SchemaField(
            description="Görüntü oluşturma için metin istemi",
            placeholder="örneğin, 'Gün batımında fütüristik bir şehir manzarası'",
            title="İstem",
        )
        ideogram_model_name: IdeogramModelName = SchemaField(
            description="Görüntü Oluşturma Modelinin adı, örneğin V_2",
            default=IdeogramModelName.V2,
            title="Görüntü Oluşturma Modeli",
            advanced=False,
        )
        aspect_ratio: AspectRatio = SchemaField(
            description="Oluşturulan görüntü için en boy oranı",
            default=AspectRatio.ORAN_1_1,
            title="En Boy Oranı",
            advanced=False,
        )
        upscale: UpscaleOption = SchemaField(
            description="Oluşturulan görüntüyü yükselt",
            default=UpscaleOption.YUKSELTME_YOK,
            title="Görüntüyü Yükselt",
            advanced=False,
        )
        magic_prompt_option: MagicPromptOption = SchemaField(
            description="İsteği geliştirmek için MagicPrompt kullanılıp kullanılmayacağı",
            default=MagicPromptOption.OTOMATIK,
            title="Magic Prompt Seçeneği",
            advanced=True,
        )
        seed: Optional[int] = SchemaField(
            description="Rastgele tohum. Tekrar üretilebilir oluşturma için ayarlayın",
            default=None,
            title="Tohum",
            advanced=True,
        )
        style_type: StyleType = SchemaField(
            description="Uygulanacak stil türü, V_2 ve üstü için geçerlidir",
            default=StyleType.OTOMATIK,
            title="Stil Türü",
            advanced=True,
        )
        negative_prompt: Optional[str] = SchemaField(
            description="Görüntüden hariç tutulacak şeylerin açıklaması",
            default=None,
            title="Negatif İstem",
            advanced=True,
        )
        color_palette_name: ColorPalettePreset = SchemaField(
            description="Renk paleti ön ayar adı, atlamak için 'Yok' seçin",
            default=ColorPalettePreset.YOK,
            title="Renk Paleti Ön Ayarı",
            advanced=True,
        )

    class Output(BlockSchema):
        result: str = SchemaField(description="Oluşturulan görüntü URL'si")
        error: str = SchemaField(description="Model çalıştırma başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="6ab085e2-20b3-4055-bc3e-08036e01eca6",
            description="Bu blok, hem basit hem de gelişmiş ayarlarla Ideogram modellerini çalıştırır.",
            categories={BlockCategory.AI},
            input_schema=IdeogramModelBlock.Input,
            output_schema=IdeogramModelBlock.Output,
            test_input={
                "ideogram_model_name": IdeogramModelName.V2,
                "prompt": "Gün batımında fütüristik bir şehir manzarası",
                "aspect_ratio": AspectRatio.ORAN_1_1,
                "upscale": UpscaleOption.YUKSELTME_YOK,
                "magic_prompt_option": MagicPromptOption.OTOMATIK,
                "seed": None,
                "style_type": StyleType.OTOMATIK,
                "negative_prompt": None,
                "color_palette_name": ColorPalettePreset.YOK,
                "credentials": TEST_CREDENTIALS_INPUT,
            },
            test_output=[
                (
                    "result",
                    "https://ideogram.ai/api/images/test-generated-image-url.png",
                ),
            ],
            test_mock={
                "run_model": lambda api_key, model_name, prompt, seed, aspect_ratio, magic_prompt_option, style_type, negative_prompt, color_palette_name: "https://ideogram.ai/api/images/test-generated-image-url.png",
                "upscale_image": lambda api_key, image_url: "https://ideogram.ai/api/images/test-upscaled-image-url.png",
            },
            test_credentials=TEST_CREDENTIALS,
        )

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        seed = input_data.seed

        # Adım 1: Görüntüyü oluştur
        result = self.run_model(
            api_key=credentials.api_key,
            model_name=input_data.ideogram_model_name.value,
            prompt=input_data.prompt,
            seed=seed,
            aspect_ratio=input_data.aspect_ratio.value,
            magic_prompt_option=input_data.magic_prompt_option.value,
            style_type=input_data.style_type.value,
            negative_prompt=input_data.negative_prompt,
            color_palette_name=input_data.color_palette_name.value,
        )

        # Adım 2: Görüntüyü yükseltme talep edilirse yükselt
        if input_data.upscale == UpscaleOption.AI_YUKSELTME:
            result = self.upscale_image(
                api_key=credentials.api_key,
                image_url=result,
            )

        yield "result", result

    def run_model(
        self,
        api_key: SecretStr,
        model_name: str,
        prompt: str,
        seed: Optional[int],
        aspect_ratio: str,
        magic_prompt_option: str,
        style_type: str,
        negative_prompt: Optional[str],
        color_palette_name: str,
    ):
        url = "https://api.ideogram.ai/generate"
        headers = {
            "Api-Key": api_key.get_secret_value(),
            "Content-Type": "application/json",
        }

        data: Dict[str, Any] = {
            "image_request": {
                "prompt": prompt,
                "model": model_name,
                "aspect_ratio": aspect_ratio,
                "magic_prompt_option": magic_prompt_option,
                "style_type": style_type,
            }
        }

        if seed is not None:
            data["image_request"]["seed"] = seed

        if negative_prompt:
            data["image_request"]["negative_prompt"] = negative_prompt

        if color_palette_name != "YOK":
            data["image_request"]["color_palette"] = {"name": color_palette_name}

        try:
            response = requests.post(url, json=data, headers=headers)
            return response.json()["data"][0]["url"]
        except RequestException as e:
            raise Exception(f"Görüntü alınamadı: {str(e)}")

    def upscale_image(self, api_key: SecretStr, image_url: str):
        url = "https://api.ideogram.ai/upscale"
        headers = {
            "Api-Key": api_key.get_secret_value(),
        }

        try:
            # Adım 1: Sağlanan URL'den görüntüyü indir
            image_response = requests.get(image_url)

            # Adım 2: İndirilen görüntüyü yükseltme API'sine gönder
            files = {
                "image_file": ("image.png", image_response.content, "image/png"),
            }

            response = requests.post(
                url,
                headers=headers,
                data={
                    "image_request": "{}",  # Boş JSON nesnesi
                },
                files=files,
            )

            return response.json()["data"][0]["url"]

        except RequestException as e:
            raise Exception(f"Görüntü yükseltilemedi: {str(e)}")
