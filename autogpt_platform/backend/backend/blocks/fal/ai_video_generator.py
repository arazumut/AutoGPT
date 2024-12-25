import logging
import time
from enum import Enum
from typing import Any

import httpx

from backend.blocks.fal._auth import (
    TEST_CREDENTIALS,
    TEST_CREDENTIALS_INPUT,
    FalCredentials,
    FalCredentialsField,
    FalCredentialsInput,
)
from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField

logger = logging.getLogger(__name__)

class FalModel(str, Enum):
    MOCHI = "fal-ai/mochi-v1"
    LUMA = "fal-ai/luma-dream-machine"

class AIVideoGeneratorBlock(Block):
    class Input(BlockSchema):
        prompt: str = SchemaField(
            description="Oluşturulacak videonun açıklaması.",
            placeholder="Bir tarlada koşan köpek.",
        )
        model: FalModel = SchemaField(
            title="FAL Modeli",
            default=FalModel.MOCHI,
            description="Video oluşturma için kullanılacak FAL modeli.",
        )
        credentials: FalCredentialsInput = FalCredentialsField()

    class Output(BlockSchema):
        video_url: str = SchemaField(description="Oluşturulan videonun URL'si.")
        error: str = SchemaField(
            description="Video oluşturma başarısız olursa hata mesajı."
        )
        logs: list[str] = SchemaField(
            description="Oluşturma ilerleme kayıtları.", optional=True
        )

    def __init__(self):
        super().__init__(
            id="530cf046-2ce0-4854-ae2c-659db17c7a46",
            description="FAL AI modellerini kullanarak video oluşturun.",
            categories={BlockCategory.AI},
            input_schema=self.Input,
            output_schema=self.Output,
            test_input={
                "prompt": "Bir tarlada koşan köpek.",
                "model": FalModel.MOCHI,
                "credentials": TEST_CREDENTIALS_INPUT,
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=[("video_url", "https://fal.media/files/example/video.mp4")],
            test_mock={
                "generate_video": lambda *args, **kwargs: "https://fal.media/files/example/video.mp4"
            },
        )

    def _get_headers(self, api_key: str) -> dict[str, str]:
        """FAL API istekleri için başlıkları alın."""
        return {
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        }

    def _submit_request(
        self, url: str, headers: dict[str, str], data: dict[str, Any]
    ) -> dict[str, Any]:
        """FAL API'ye istek gönderin."""
        try:
            response = httpx.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"FAL API isteği başarısız oldu: {str(e)}")
            raise RuntimeError(f"İstek gönderilemedi: {str(e)}")

    def _poll_status(self, status_url: str, headers: dict[str, str]) -> dict[str, Any]:
        """Tamamlanana veya başarısız olana kadar durum uç noktasını sorgulayın."""
        try:
            response = httpx.get(status_url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Durum alınamadı: {str(e)}")
            raise RuntimeError(f"Durum alınamadı: {str(e)}")

    def generate_video(self, input_data: Input, credentials: FalCredentials) -> str:
        """Belirtilen FAL modelini kullanarak video oluşturun."""
        base_url = "https://queue.fal.run"
        api_key = credentials.api_key.get_secret_value()
        headers = self._get_headers(api_key)

        # Oluşturma isteğini gönder
        submit_url = f"{base_url}/{input_data.model.value}"
        submit_data = {"prompt": input_data.prompt}

        seen_logs = set()

        try:
            # Kuyruğa istek gönder
            submit_response = httpx.post(submit_url, headers=headers, json=submit_data)
            submit_response.raise_for_status()
            request_data = submit_response.json()

            # İlk yanıttan request_id ve url'leri alın
            request_id = request_data.get("request_id")
            status_url = request_data.get("status_url")
            result_url = request_data.get("response_url")

            if not all([request_id, status_url, result_url]):
                raise ValueError("Gönderim yanıtında gerekli veriler eksik")

            # Durumu üstel geri çekilme ile sorgulayın
            max_attempts = 30
            attempt = 0
            base_wait_time = 5

            while attempt < max_attempts:
                status_response = httpx.get(f"{status_url}?logs=1", headers=headers)
                status_response.raise_for_status()
                status_data = status_response.json()

                # Yalnızca yeni günlükleri işleyin
                logs = status_data.get("logs", [])
                if logs and isinstance(logs, list):
                    for log in logs:
                        if isinstance(log, dict):
                            # Bu günlük girdisi için benzersiz bir anahtar oluşturun
                            log_key = (
                                f"{log.get('timestamp', '')}-{log.get('message', '')}"
                            )
                            if log_key not in seen_logs:
                                seen_logs.add(log_key)
                                message = log.get("message", "")
                                if message:
                                    logger.debug(
                                        f"[FAL Oluşturma] [{log.get('level', 'INFO')}] [{log.get('source', '')}] [{log.get('timestamp', '')}] {message}"
                                    )

                status = status_data.get("status")
                if status == "COMPLETED":
                    # Nihai sonucu alın
                    result_response = httpx.get(result_url, headers=headers)
                    result_response.raise_for_status()
                    result_data = result_response.json()

                    if "video" not in result_data or not isinstance(
                        result_data["video"], dict
                    ):
                        raise ValueError("Geçersiz yanıt formatı - video verisi eksik")

                    video_url = result_data["video"].get("url")
                    if not video_url:
                        raise ValueError("Yanıtta video URL'si yok")

                    return video_url

                elif status == "FAILED":
                    error_msg = status_data.get("error", "Hata ayrıntıları sağlanmadı")
                    raise RuntimeError(f"Video oluşturma başarısız oldu: {error_msg}")
                elif status == "IN_QUEUE":
                    position = status_data.get("queue_position", "bilinmiyor")
                    logger.debug(
                        f"[FAL Oluşturma] Durum: Kuyrukta, pozisyon: {position}"
                    )
                elif status == "IN_PROGRESS":
                    logger.debug(
                        "[FAL Oluşturma] Durum: İstek işleniyor..."
                    )
                else:
                    logger.info(f"[FAL Oluşturma] Durum: Bilinmeyen durum: {status}")

                wait_time = min(base_wait_time * (2**attempt), 60)  # 60 saniyede sınırla
                time.sleep(wait_time)
                attempt += 1

            raise RuntimeError("Maksimum sorgulama denemesi aşıldı")

        except httpx.HTTPError as e:
            raise RuntimeError(f"API isteği başarısız oldu: {str(e)}")

    def run(
        self, input_data: Input, *, credentials: FalCredentials, **kwargs
    ) -> BlockOutput:
        try:
            video_url = self.generate_video(input_data, credentials)
            yield "video_url", video_url
        except Exception as e:
            error_message = str(e)
            yield "error", error_message
