from typing import Any, Literal

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

# Test için kullanılacak API anahtarı
TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="unreal_speech",
    api_key=SecretStr("mock-unreal-speech-api-key"),
    title="Mock Unreal Speech API key",
    expires_at=None,
)
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.type,
}

class UnrealTextToSpeechBlock(Block):
    class Input(BlockSchema):
        text: str = SchemaField(
            description="Konuşmaya dönüştürülecek metin",
            placeholder="Konuşmaya dönüştürmek istediğiniz metni girin",
        )
        voice_id: str = SchemaField(
            description="Metni konuşmaya dönüştürmek için kullanılacak ses kimliği",
            placeholder="Scarlett",
            default="Scarlett",
        )
        credentials: CredentialsMetaInput[
            Literal[ProviderName.UNREAL_SPEECH], Literal["api_key"]
        ] = CredentialsField(
            description="Unreal Speech entegrasyonu, üzerinde kullanıldığı bloklar için yeterli izinlere sahip herhangi bir API anahtarı ile kullanılabilir.",
        )

    class Output(BlockSchema):
        mp3_url: str = SchemaField(description="Oluşturulan MP3 dosyasının URL'si")
        error: str = SchemaField(description="API çağrısı başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="4ff1ff6d-cc40-4caa-ae69-011daa20c378",
            description="Unreal Speech API kullanarak metni konuşmaya dönüştürür",
            categories={BlockCategory.AI, BlockCategory.TEXT},
            input_schema=UnrealTextToSpeechBlock.Input,
            output_schema=UnrealTextToSpeechBlock.Output,
            test_input={
                "text": "Bu, metni konuşmaya dönüştürme API'sinin bir testidir.",
                "voice_id": "Scarlett",
                "credentials": TEST_CREDENTIALS_INPUT,
            },
            test_output=[("mp3_url", "https://example.com/test.mp3")],
            test_mock={
                "call_unreal_speech_api": lambda *args, **kwargs: {
                    "OutputUri": "https://example.com/test.mp3"
                }
            },
            test_credentials=TEST_CREDENTIALS,
        )

    @staticmethod
    def call_unreal_speech_api(
        api_key: SecretStr, text: str, voice_id: str
    ) -> dict[str, Any]:
        url = "https://api.v7.unrealspeech.com/speech"
        headers = {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }
        data = {
            "Text": text,
            "VoiceId": voice_id,
            "Bitrate": "192k",
            "Speed": "0",
            "Pitch": "1",
            "TimestampType": "sentence",
        }

        response = requests.post(url, headers=headers, json=data)
        return response.json()

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        api_response = self.call_unreal_speech_api(
            credentials.api_key,
            input_data.text,
            input_data.voice_id,
        )
        yield "mp3_url", api_response["OutputUri"]
