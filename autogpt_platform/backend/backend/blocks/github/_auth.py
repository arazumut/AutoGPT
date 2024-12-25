from typing import Literal

from pydantic import SecretStr

from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    OAuth2Credentials,
)
from backend.integrations.providers import ProviderName
from backend.util.settings import Secrets

secrets = Secrets()
GITHUB_OAUTH_IS_CONFIGURED = bool(
    secrets.github_client_id and secrets.github_client_secret
)

GithubCredentials = APIKeyCredentials | OAuth2Credentials
GithubCredentialsInput = CredentialsMetaInput[
    Literal[ProviderName.GITHUB],
    Literal["api_key", "oauth2"] if GITHUB_OAUTH_IS_CONFIGURED else Literal["api_key"],
]


def GithubCredentialsField(scope: str) -> GithubCredentialsInput:
    """
    Bir GitHub kimlik bilgisi girişi oluşturur.

    Parametreler:
        scope: Bloğun çalışması için gereken yetkilendirme kapsamı. ([mevcut kapsamların listesi](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps#available-scopes))
    """  # noqa
    return CredentialsField(
        required_scopes={scope},
        description="GitHub entegrasyonu OAuth ile veya bloklarda kullanılan yeterli izinlere sahip herhangi bir API anahtarı ile kullanılabilir.",
    )


TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="github",
    api_key=SecretStr("mock-github-api-key"),
    title="Mock GitHub API anahtarı",
    expires_at=None,
)
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.type,
}
