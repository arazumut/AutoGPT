from typing import Any, Dict

import jwt

from .config import settings


def jwt_tokenini_parse_et(token: str) -> Dict[str, Any]:
    """
    Bir JWT tokenini ayrıştır ve doğrula.

    :param token: Ayrıştırılacak token
    :return: Ayrıştırılmış payload
    :raises ValueError: Token geçersiz veya süresi dolmuşsa
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Tokenin süresi dolmuş")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Geçersiz token: {str(e)}")
