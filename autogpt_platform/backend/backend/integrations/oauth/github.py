import time
from typing import Optional, Union
from urllib.parse import urlencode

from backend.data.model import OAuth2Credentials
from backend.integrations.providers import ProviderName
from backend.util.request import requests

from .base import BaseOAuthHandler


class GitHubOAuthHandler(BaseOAuthHandler):
    """
    Belgelere dayanarak:
    - [OAuth uygulamalarını yetkilendirme - GitHub Belgeleri](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps)
    - [Kullanıcı erişim belirteçlerini yenileme - GitHub Belgeleri](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/refreshing-user-access-tokens)

    Notlar:
    - Varsayılan olarak, GitHub Uygulamalarında belirteç süresi dolumu devre dışıdır. Bu, erişim
      belirtecinin süresinin dolmadığı ve yetkilendirme akışı tarafından yenileme belirteci döndürülmediği anlamına gelir.
    - Belirteç süresi dolumu etkinleştirildiğinde, mevcut belirteçler süresi dolmayan olarak kalacaktır.
    - Belirteç süresi dolumu devre dışı bırakıldığında, belirteç yenilemeleri *yenileme belirteci olmadan* süresi dolmayan bir erişim belirteci döndürecektir.
    """

    PROVIDER_NAME = ProviderName.GITHUB

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.auth_base_url = "https://github.com/login/oauth/authorize"
        self.token_url = "https://github.com/login/oauth/access_token"
        self.revoke_url = "https://api.github.com/applications/{client_id}/token"

    def get_login_url(self, scopes: list[str], state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
        }
        return f"{self.auth_base_url}?{urlencode(params)}"

    def exchange_code_for_tokens(
        self, code: str, scopes: list[str]
    ) -> OAuth2Credentials:
        return self._request_tokens({"code": code, "redirect_uri": self.redirect_uri})

    def revoke_tokens(self, credentials: OAuth2Credentials) -> bool:
        if not credentials.access_token:
            raise ValueError("İptal edilecek erişim belirteci yok")

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        requests.delete(
            url=self.revoke_url.format(client_id=self.client_id),
            auth=(self.client_id, self.client_secret),
            headers=headers,
            json={"access_token": credentials.access_token.get_secret_value()},
        )
        return True

    def _refresh_tokens(self, credentials: OAuth2Credentials) -> OAuth2Credentials:
        if not credentials.refresh_token:
            return credentials

        return self._request_tokens(
            {
                "refresh_token": credentials.refresh_token.get_secret_value(),
                "grant_type": "refresh_token",
            }
        )

    def _request_tokens(
        self,
        params: dict[str, str],
        current_credentials: Optional[OAuth2Credentials] = None,
    ) -> OAuth2Credentials:
        request_body = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            **params,
        }
        headers = {"Accept": "application/json"}
        response = requests.post(self.token_url, data=request_body, headers=headers)
        token_data: dict = response.json()

        username = self._request_username(token_data["access_token"])

        now = int(time.time())
        new_credentials = OAuth2Credentials(
            provider=self.PROVIDER_NAME,
            title=current_credentials.title if current_credentials else None,
            username=username,
            access_token=token_data["access_token"],
            scopes=(
                token_data.get("scope", "").split(",")
                or (current_credentials.scopes if current_credentials else [])
            ),
            refresh_token=token_data.get("refresh_token"),
            access_token_expires_at=(
                now + expires_in
                if (expires_in := token_data.get("expires_in", None))
                else None
            ),
            refresh_token_expires_at=(
                now + expires_in
                if (expires_in := token_data.get("refresh_token_expires_in", None))
                else None
            ),
        )
        if current_credentials:
            new_credentials.id = current_credentials.id
        return new_credentials

    def _request_username(self, access_token: str) -> Union[str, None]:
        url = "https://api.github.com/user"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {access_token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        response = requests.get(url, headers=headers)

        if not response.ok:
            return None

        return response.json().get("login")
