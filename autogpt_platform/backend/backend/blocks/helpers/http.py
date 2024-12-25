from typing import Any, Optional
from backend.util.request import requests

class GetIstegi:
    @classmethod
    def get_istegi(
        cls, url: str, basliklar: Optional[dict] = None, json: bool = False
    ) -> Any:
        if basliklar is None:
            basliklar = {}
        yanit = requests.get(url, headers=basliklar)
        return yanit.json() if json else yanit.text
