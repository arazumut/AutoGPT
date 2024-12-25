from typing import Literal
from pydantic import SecretStr
from backend.data.model import APIKeyCredentials, CredentialsField, CredentialsMetaInput
from backend.integrations.providers import ProviderName

# Exa API Anahtar Kimlik Bilgileri
ExaCredentials = APIKeyCredentials
ExaCredentialsInput = CredentialsMetaInput[
    Literal[ProviderName.EXA],
    Literal["api_key"],
]

# Test Kimlik Bilgileri
TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="exa",
    api_key=SecretStr("mock-exa-api-key"),
    title="Mock Exa API key",
    expires_at=None,
)

# Test Kimlik Bilgileri Girişi
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.title,
}

def ExaCredentialsField() -> ExaCredentialsInput:
    """Bir Exa kimlik bilgisi girişi oluşturur."""
    return CredentialsField(description="Exa entegrasyonu bir API Anahtarı gerektirir.")
