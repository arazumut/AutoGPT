from typing import Literal
from pydantic import SecretStr
from backend.data.model import APIKeyCredentials, CredentialsField, CredentialsMetaInput
from backend.integrations.providers import ProviderName

# HubSpot API Anahtarı Kimlik Bilgileri
HubSpotCredentials = APIKeyCredentials

# HubSpot Kimlik Bilgileri Girişi
HubSpotCredentialsInput = CredentialsMetaInput[
    Literal[ProviderName.HUBSPOT],
    Literal["api_key"],
]

def HubSpotCredentialsField() -> HubSpotCredentialsInput:
    """Bir HubSpot kimlik bilgileri girişi oluşturur."""
    return CredentialsField(
        description="HubSpot entegrasyonu bir API Anahtarı gerektirir.",
    )

# Test Kimlik Bilgileri
TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="hubspot",
    api_key=SecretStr("mock-hubspot-api-key"),
    title="Mock HubSpot API anahtarı",
    expires_at=None,
)

# Test Kimlik Bilgileri Girişi
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.title,
}
