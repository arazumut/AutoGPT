from typing import Literal
from pydantic import SecretStr
from backend.data.model import CredentialsField, CredentialsMetaInput, OAuth2Credentials
from backend.integrations.providers import ProviderName
from backend.util.settings import Secrets

# Google OAuth yapılandırmasının kontrolü
secrets = Secrets()
GOOGLE_OAUTH_IS_CONFIGURED = bool(
    secrets.google_client_id and secrets.google_client_secret
)

GoogleCredentials = OAuth2Credentials
GoogleCredentialsInput = CredentialsMetaInput[
    Literal[ProviderName.GOOGLE], Literal["oauth2"]
]

def GoogleCredentialsField(scopes: list[str]) -> GoogleCredentialsInput:
    """
    Bir Google kimlik bilgisi girişi oluşturur.

    Parametreler:
        scopes: Bloğun çalışması için gereken yetkilendirme kapsamları.
    """
    return CredentialsField(
        required_scopes=set(scopes),
        description="Google entegrasyonu OAuth2 kimlik doğrulaması gerektirir.",
    )

# Test kimlik bilgileri
TEST_CREDENTIALS = OAuth2Credentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="google",
    access_token=SecretStr("mock-google-access-token"),
    refresh_token=SecretStr("mock-google-refresh-token"),
    access_token_expires_at=1234567890,
    scopes=[
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ],
    title="Mock Google OAuth2 Kimlik Bilgileri",
    username="mock-google-username",
    refresh_token_expires_at=1234567890,
)

# Test kimlik bilgisi girişi
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.title,
}
