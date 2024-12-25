from typing import Literal

from pydantic import SecretStr

from backend.data.model import APIKeyCredentials, CredentialsField, CredentialsMetaInput
from backend.integrations.providers import ProviderName

FalKimlikBilgileri = APIKeyCredentials
FalKimlikBilgileriGirdisi = CredentialsMetaInput[
    Literal[ProviderName.FAL],
    Literal["api_key"],
]

TEST_KIMLIK_BILGILERI = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="fal",
    api_key=SecretStr("mock-fal-api-key"),
    title="Mock FAL API anahtarı",
    expires_at=None,
)
TEST_KIMLIK_BILGILERI_GIRDISI = {
    "provider": TEST_KIMLIK_BILGILERI.provider,
    "id": TEST_KIMLIK_BILGILERI.id,
    "type": TEST_KIMLIK_BILGILERI.type,
    "title": TEST_KIMLIK_BILGILERI.title,
}


def FalKimlikBilgileriAlani() -> FalKimlikBilgileriGirdisi:
    """
    Bir blok üzerinde FAL kimlik bilgileri girdisi oluşturur.
    """
    return CredentialsField(
        description="FAL entegrasyonu bir API Anahtarı ile kullanılabilir.",
    )
