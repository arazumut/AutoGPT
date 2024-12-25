from dataclasses import dataclass

# Varsayılan kullanıcı ID'si ve e-posta adresi
VARSAYILAN_KULLANICI_ID = "3e53486c-cf57-477e-ba2a-cb02dc828e1a"
VARSAYILAN_EPOSTA = "default@example.com"

# Pydantic bağımlılığını eklememek için dataclass kullanıyoruz
@dataclass(frozen=True)
class Kullanici:
    kullanici_id: str
    eposta: str
    telefon_numarasi: str
    rol: str

    @classmethod
    def yukle(cls, yuk):
        return cls(
            kullanici_id=yuk["sub"],
            eposta=yuk.get("email", ""),
            telefon_numarasi=yuk.get("phone", ""),
            rol=yuk["role"],
        )
