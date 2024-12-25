import fastapi

from .config import Ayarlar
from .middleware import kimlik_dogrulama_arabirimi
from .models import VARSAYILAN_KULLANICI_ID, Kullanıcı


def kullanici_gerektirir(payload: dict = fastapi.Depends(kimlik_dogrulama_arabirimi)) -> Kullanıcı:
    return kullaniciyi_dogrula(payload, sadece_admin=False)


def admin_kullanici_gerektirir(
    payload: dict = fastapi.Depends(kimlik_dogrulama_arabirimi),
) -> Kullanıcı:
    return kullaniciyi_dogrula(payload, sadece_admin=True)


def kullaniciyi_dogrula(payload: dict | None, sadece_admin: bool) -> Kullanıcı:
    if not payload:
        if Ayarlar.KIMLIK_DOGRULAMA_ETKIN:
            raise fastapi.HTTPException(
                status_code=401, detail="Yetkilendirme başlığı eksik"
            )
        # Kimlik doğrulama devre dışı bırakıldığında bu durumu ele alır
        payload = {"sub": VARSAYILAN_KULLANICI_ID, "rol": "admin"}

    

    kullanici_id = payload.get("sub")

    if not kullanici_id:
        raise fastapi.HTTPException(
            status_code=401, detail="Token'da Kullanıcı ID bulunamadı"
        )

    if sadece_admin and payload["rol"] != "admin":
        raise fastapi.HTTPException(status_code=403, detail="Admin erişimi gerekli")

    return Kullanıcı.payloaddan(payload)


def kullanici_id_al(payload: dict = fastapi.Depends(kimlik_dogrulama_arabirimi)) -> str:
    kullanici_id = payload.get("sub")
    if not kullanici_id:
        raise fastapi.HTTPException(
            status_code=401, detail="Token'da Kullanıcı ID bulunamadı"
        )
    return kullanici_id
