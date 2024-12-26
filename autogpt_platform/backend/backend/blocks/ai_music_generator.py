import logging
import time
from enum import Enum
from typing import Literal

import replicate
from pydantic import SecretStr

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
)
from backend.integrations.providers import ProviderName

logger = logging.getLogger(__name__)

# Test API anahtarı
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

# Model sürüm enum
class MusicGenModelVersion(str, Enum):
    STEREO_LARGE = "stereo-large"
    MELODY_LARGE = "melody-large"
    LARGE = "large"

# Ses formatı enum
class AudioFormat(str, Enum):
    WAV = "wav"
    MP3 = "mp3"

# Normalizasyon stratejisi enum
class NormalizationStrategy(str, Enum):
    LOUDNESS = "loudness"
    CLIP = "clip"
    PEAK = "peak"
    RMS = "rms"

class AIMusicGeneratorBlock(Block):
    class Input(BlockSchema):
        credentials: CredentialsMetaInput[
            Literal[ProviderName.REPLICATE], Literal["api_key"]
        ] = CredentialsField(
            description="Replicate entegrasyonu, kullanıldığı bloklar için yeterli izinlere sahip herhangi bir API anahtarı ile kullanılabilir.",
        )
        prompt: str = SchemaField(
            description="Oluşturmak istediğiniz müziğin bir açıklaması",
            placeholder="Örneğin, 'Ağır baslı neşeli bir elektronik dans parçası'",
            title="Açıklama",
        )
        music_gen_model_version: MusicGenModelVersion = SchemaField(
            description="Oluşturma için kullanılacak model",
            default=MusicGenModelVersion.STEREO_LARGE,
            title="Model Sürümü",
        )
        duration: int = SchemaField(
            description="Oluşturulan sesin süresi (saniye cinsinden)",
            default=8,
            title="Süre",
        )
        temperature: float = SchemaField(
            description="Örnekleme sürecinin 'tutuculuğunu' kontrol eder. Daha yüksek sıcaklık daha fazla çeşitlilik demektir",
            default=1.0,
            title="Sıcaklık",
        )
        top_k: int = SchemaField(
            description="Örneklemeyi en olası k token ile sınırlar",
            default=250,
            title="Top K",
        )
        top_p: float = SchemaField(
            description="Örneklemeyi kümülatif olasılığı p olan tokenlerle sınırlar. 0'a ayarlandığında (varsayılan), top_k örnekleme kullanılır",
            default=0.0,
            title="Top P",
        )
        classifier_free_guidance: int = SchemaField(
            description="Girdilerin çıktı üzerindeki etkisini artırır. Daha yüksek değerler, girdilere daha sıkı uyan düşük varyanslı çıktılar üretir",
            default=3,
            title="Sınıflandırıcı Serbest Rehberlik",
        )
        output_format: AudioFormat = SchemaField(
            description="Oluşturulan sesin çıkış formatı",
            default=AudioFormat.WAV,
            title="Çıkış Formatı",
        )
        normalization_strategy: NormalizationStrategy = SchemaField(
            description="Sesin normalleştirilmesi için strateji",
            default=NormalizationStrategy.LOUDNESS,
            title="Normalizasyon Stratejisi",
        )

    class Output(BlockSchema):
        result: str = SchemaField(description="Oluşturulan ses dosyasının URL'si")
        error: str = SchemaField(description="Model çalıştırma başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="44f6c8ad-d75c-4ae1-8209-aad1c0326928",
            description="Bu blok, Meta'nın MusicGen modelini kullanarak Replicate üzerinde müzik oluşturur.",
            categories={BlockCategory.AI},
            input_schema=AIMusicGeneratorBlock.Input,
            output_schema=AIMusicGeneratorBlock.Output,
            test_input={
                "credentials": TEST_CREDENTIALS_INPUT,
                "prompt": "Ağır baslı neşeli bir elektronik dans parçası",
                "music_gen_model_version": MusicGenModelVersion.STEREO_LARGE,
                "duration": 8,
                "temperature": 1.0,
                "top_k": 250,
                "top_p": 0.0,
                "classifier_free_guidance": 3,
                "output_format": AudioFormat.WAV,
                "normalization_strategy": NormalizationStrategy.LOUDNESS,
            },
            test_output=[
                (
                    "result",
                    "https://replicate.com/output/generated-audio-url.wav",
                ),
            ],
            test_mock={
                "run_model": lambda api_key, music_gen_model_version, prompt, duration, temperature, top_k, top_p, classifier_free_guidance, output_format, normalization_strategy: "https://replicate.com/output/generated-audio-url.wav",
            },
            test_credentials=TEST_CREDENTIALS,
        )

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        max_retries = 3
        retry_delay = 5  # saniye
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.debug(
                    f"[AIMusicGeneratorBlock] - Model çalıştırılıyor (deneme {attempt + 1})"
                )
                result = self.run_model(
                    api_key=credentials.api_key,
                    music_gen_model_version=input_data.music_gen_model_version,
                    prompt=input_data.prompt,
                    duration=input_data.duration,
                    temperature=input_data.temperature,
                    top_k=input_data.top_k,
                    top_p=input_data.top_p,
                    classifier_free_guidance=input_data.classifier_free_guidance,
                    output_format=input_data.output_format,
                    normalization_strategy=input_data.normalization_strategy,
                )
                if result and result != "No output received":
                    yield "result", result
                    return
                else:
                    last_error = "Model boş veya geçersiz yanıt döndürdü"
                    raise ValueError(last_error)
            except Exception as e:
                last_error = f"Beklenmeyen hata: {str(e)}"
                logger.error(f"[AIMusicGeneratorBlock] - Hata: {last_error}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue

        # Tüm denemeler tükendiyse, hatayı döndür
        yield "error", f"{max_retries} denemeden sonra başarısız oldu. Son hata: {last_error}"

    def run_model(
        self,
        api_key: SecretStr,
        music_gen_model_version: MusicGenModelVersion,
        prompt: str,
        duration: int,
        temperature: float,
        top_k: int,
        top_p: float,
        classifier_free_guidance: int,
        output_format: AudioFormat,
        normalization_strategy: NormalizationStrategy,
    ):
        # Replicate istemcisini API anahtarı ile başlat
        client = replicate.Client(api_token=api_key.get_secret_value())

        # Modeli parametrelerle çalıştır
        output = client.run(
            "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
            input={
                "prompt": prompt,
                "music_gen_model_version": music_gen_model_version,
                "duration": duration,
                "temperature": temperature,
                "top_k": top_k,
                "top_p": top_p,
                "classifier_free_guidance": classifier_free_guidance,
                "output_format": output_format,
                "normalization_strategy": normalization_strategy,
            },
        )

        # Çıktıyı işle
        if isinstance(output, list) and len(output) > 0:
            result_url = output[0]  # Çıktı bir liste ise, ilk öğeyi al
        elif isinstance(output, str):
            result_url = output  # Çıktı bir string ise, doğrudan kullan
        else:
            result_url = "No output received"  # Çıktı beklenildiği gibi değilse yedek mesaj

        return result_url
