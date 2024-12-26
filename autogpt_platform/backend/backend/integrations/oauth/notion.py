from base64 import b64encode
from urllib.parse import urlencode

from backend.data.model import OAuth2Credentials
from backend.integrations.providers import ProviderName
from backend.util.request import requests

from .base import BaseOAuthHandler


class NotionOAuthHandler(BaseOAuthHandler):
    """
    https://developers.notion.com/docs/authorization adresindeki dokümantasyona dayanmaktadır.

    Notlar:
    - Notion, süresi dolmayan erişim belirteçleri kullanır ve bu nedenle yenileme akışı yoktur
    - Notion, kapsamları kullanmaz
    """

    PROVIDER_NAME = ProviderName.NOTION

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_base_url = "https://api.notion.com/v1/oauth/authorize"
        self.token_url = "https://api.notion.com/v1/oauth/token"

    def get_login_url(self, scopes: list[str], state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "owner": "user",
            "state": state,
        }
        return f"{self.auth_base_url}?{urlencode(params)}"

    def exchange_code_for_tokens(
        self, code: str, scopes: list[str]
    ) -> OAuth2Credentials:
        request_body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        auth_str = b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_str}",
            "Accept": "application/json",
        }
        response = requests.post(self.token_url, json=request_body, headers=headers)
        token_data = response.json()
        # E-posta yalnızca bot olmayan kullanıcılar için kullanılabilir
        email = (
            token_data["owner"]["person"]["email"]
            if "person" in token_data["owner"]
            and "email" in token_data["owner"]["person"]
            else None
        )

        return OAuth2Credentials(
            provider=self.PROVIDER_NAME,
            title=token_data.get("workspace_name"),
            username=email,
            access_token=token_data["access_token"],
            refresh_token=None,
            access_token_expires_at=None,  # Notion belirteçleri süresi dolmaz
            refresh_token_expires_at=None,
            scopes=[],
            metadata={
                "owner": token_data["owner"],
                "bot_id": token_data["bot_id"],
                "workspace_id": token_data["workspace_id"],
                "workspace_name": token_data.get("workspace_name"),
                "workspace_icon": token_data.get("workspace_icon"),
            },
        )

    def revoke_tokens(self, credentials: OAuth2Credentials) -> bool:
        # Notion belirteç iptalini desteklemez
        return False

    def _refresh_tokens(self, credentials: OAuth2Credentials) -> OAuth2Credentials:
        # Notion belirteç yenilemeyi desteklemez
        return credentials

    def needs_refresh(self, credentials: OAuth2Credentials) -> bool:
        # Notion erişim belirteçleri süresi dolmaz
        return False
