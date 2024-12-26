import time
from typing import Literal

from pydantic import SecretStr

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
)
from backend.integrations.providers import ProviderName
from backend.util.request import requests

# Test için kullanılacak API anahtar bilgileri
TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="d_id",
    api_key=SecretStr("mock-d-id-api-key"),
    title="Mock D-ID API key",
    expires_at=None,
)
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.type,
}

class KonuşanAvatarVideoOluşturmaBloğu(Block):
    class Girdi(BlockSchema):
        kimlik_bilgileri: CredentialsMetaInput[
            Literal[ProviderName.D_ID], Literal["api_key"]
        ] = CredentialsField(
            description="D-ID entegrasyonu, bloklar üzerinde kullanılmak üzere yeterli izinlere sahip herhangi bir API anahtarı ile kullanılabilir.",
        )
        senaryo_girdisi: str = SchemaField(
            description="Senaryo için metin girdisi",
            placeholder="AutoGPT'ye hoş geldiniz",
        )
        sağlayıcı: Literal["microsoft", "elevenlabs", "amazon"] = SchemaField(
            description="Kullanılacak ses sağlayıcısı", default="microsoft"
        )
        ses_id: str = SchemaField(
            description="Kullanılacak ses kimliği, ses listesini [buradan](https://docs.agpt.co/server/d_id) alın",
            default="en-US-JennyNeural",
        )
        sunucu_id: str = SchemaField(
            description="Kullanılacak sunucu kimliği", default="amy-Aq6OmGZnMt"
        )
        sürücü_id: str = SchemaField(
            description="Kullanılacak sürücü kimliği", default="Vcq0R4a8F0"
        )
        sonuç_formatı: Literal["mp4", "gif", "wav"] = SchemaField(
            description="İstenen sonuç formatı", default="mp4"
        )
        kırpma_türü: Literal["geniş", "kare", "dikey"] = SchemaField(
            description="Sunucu için kırpma türü", default="geniş"
        )
        altyazılar: bool = SchemaField(
            description="Altyazıların dahil edilip edilmeyeceği", default=False
        )
        ssml: bool = SchemaField(description="Girdinin SSML olup olmadığı", default=False)
        maksimum_yoklama_denemesi: int = SchemaField(
            description="Maksimum yoklama denemesi sayısı", default=30, ge=5
        )
        yoklama_aralığı: int = SchemaField(
            description="Yoklama denemeleri arasındaki aralık (saniye)", default=10, ge=5
        )

    class Çıktı(BlockSchema):
        video_url: str = SchemaField(description="Oluşturulan videonun URL'si")
        hata: str = SchemaField(description="İstek başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="98c6f503-8c47-4b1c-a96d-351fc7c87dab",
            description="Bu blok, D-ID ile entegre olarak video klipler oluşturur ve URL'lerini alır.",
            categories={BlockCategory.AI},
            input_schema=KonuşanAvatarVideoOluşturmaBloğu.Girdi,
            output_schema=KonuşanAvatarVideoOluşturmaBloğu.Çıktı,
            test_input={
                "kimlik_bilgileri": TEST_CREDENTIALS_INPUT,
                "senaryo_girdisi": "AutoGPT'ye hoş geldiniz",
                "ses_id": "en-US-JennyNeural",
                "sunucu_id": "amy-Aq6OmGZnMt",
                "sürücü_id": "Vcq0R4a8F0",
                "sonuç_formatı": "mp4",
                "kırpma_türü": "geniş",
                "altyazılar": False,
                "ssml": False,
                "maksimum_yoklama_denemesi": 5,
                "yoklama_aralığı": 5,
            },
            test_output=[
                (
                    "video_url",
                    "https://d-id.com/api/clips/abcd1234-5678-efgh-ijkl-mnopqrstuvwx/video",
                ),
            ],
            test_mock={
                "create_clip": lambda *args, **kwargs: {
                    "id": "abcd1234-5678-efgh-ijkl-mnopqrstuvwx",
                    "status": "created",
                },
                "get_clip_status": lambda *args, **kwargs: {
                    "status": "done",
                    "result_url": "https://d-id.com/api/clips/abcd1234-5678-efgh-ijkl-mnopqrstuvwx/video",
                },
            },
            test_credentials=TEST_CREDENTIALS,
        )

    def klip_oluştur(self, api_key: SecretStr, payload: dict) -> dict:
        url = "https://api.d-id.com/clips"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Basic {api_key.get_secret_value()}",
        }
        response = requests.post(url, json=payload, headers=headers)
        return response.json()

    def klip_durumu_al(self, api_key: SecretStr, clip_id: str) -> dict:
        url = f"https://api.d-id.com/clips/{clip_id}"
        headers = {
            "accept": "application/json",
            "authorization": f"Basic {api_key.get_secret_value()}",
        }
        response = requests.get(url, headers=headers)
        return response.json()

    def çalıştır(
        self, girdi_verisi: Girdi, *, kimlik_bilgileri: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        # Klip oluştur
        payload = {
            "script": {
                "type": "text",
                "subtitles": str(girdi_verisi.altyazılar).lower(),
                "provider": {
                    "type": girdi_verisi.sağlayıcı,
                    "voice_id": girdi_verisi.ses_id,
                },
                "ssml": str(girdi_verisi.ssml).lower(),
                "input": girdi_verisi.senaryo_girdisi,
            },
            "config": {"result_format": girdi_verisi.sonuç_formatı},
            "presenter_config": {"crop": {"type": girdi_verisi.kırpma_türü}},
            "presenter_id": girdi_verisi.sunucu_id,
            "driver_id": girdi_verisi.sürücü_id,
        }

        response = self.klip_oluştur(kimlik_bilgileri.api_key, payload)
        clip_id = response["id"]

        # Klip durumu için yoklama yap
        for _ in range(girdi_verisi.maksimum_yoklama_denemesi):
            status_response = self.klip_durumu_al(kimlik_bilgileri.api_key, clip_id)
            if status_response["status"] == "done":
                yield "video_url", status_response["result_url"]
                return
            elif status_response["status"] == "error":
                raise RuntimeError(
                    f"Klip oluşturma başarısız: {status_response.get('error', 'Bilinmeyen hata')}"
                )

            time.sleep(girdi_verisi.yoklama_aralığı)

        raise TimeoutError("Klip oluşturma zaman aşımına uğradı")
