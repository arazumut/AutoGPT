from enum import Enum
from typing import Literal

from pydantic import BaseModel, SecretStr

from backend.data.model import APIKeyCredentials, CredentialsField, CredentialsMetaInput
from backend.integrations.providers import ProviderName

# Slant3D için kimlik bilgileri girişi
Slant3DKimlikBilgileriGirişi = CredentialsMetaInput[
    Literal[ProviderName.SLANT3D], Literal["api_key"]
]

# Slant3D kimlik bilgileri alanı
def Slant3DKimlikBilgileriAlanı() -> Slant3DKimlikBilgileriGirişi:
    return CredentialsField(description="Slant3D API anahtarı ile kimlik doğrulama")

# Test kimlik bilgileri
TEST_KIMLIK_BILGILERI = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="slant3d",
    api_key=SecretStr("mock-slant3d-api-key"),
    title="Mock Slant3D API anahtarı",
    expires_at=None,
)

# Test kimlik bilgileri girişi
TEST_KIMLIK_BILGILERI_GIRISI = {
    "provider": TEST_KIMLIK_BILGILERI.provider,
    "id": TEST_KIMLIK_BILGILERI.id,
    "type": TEST_KIMLIK_BILGILERI.type,
    "title": TEST_KIMLIK_BILGILERI.title,
}

# Müşteri detayları modeli
class MusteriDetaylari(BaseModel):
    isim: str
    email: str
    telefon: str
    adres: str
    sehir: str
    eyalet: str
    posta_kodu: str
    ulke_iso: str = "US"
    konut_mu: bool = True

# Renk enum sınıfı
class Renk(Enum):
    BEYAZ = "white"
    SIYAH = "black"

# Profil enum sınıfı
class Profil(Enum):
    PLA = "PLA"
    PETG = "PETG"

# Sipariş öğesi modeli
class SiparisOgeleri(BaseModel):
    dosya_url: str
    miktar: str  # API spesifikasyonuna göre string
    renk: Renk = Renk.BEYAZ
    profil: Profil = Profil.PLA

# Filament modeli
class Filament(BaseModel):
    filament: str
    hexRenk: str
    renkEtiketi: str
    profil: str
