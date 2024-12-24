import hashlib
import secrets
from typing import NamedTuple

class APIAnahtarKapsayıcı(NamedTuple):
    """API anahtar parçaları için kapsayıcı."""

    ham: str
    önek: str
    sonek: str
    hash: str

class APIAnahtarYönetici:
    ÖNEK: str = "agpt_"
    ÖNEK_UZUNLUK: int = 8
    SONEK_UZUNLUK: int = 8

    def api_anahtarı_oluştur(self) -> APIAnahtarKapsayıcı:
        """Tüm parçalarıyla yeni bir API anahtarı oluştur."""
        ham_anahtar = f"{self.ÖNEK}{secrets.token_urlsafe(32)}"
        return APIAnahtarKapsayıcı(
            ham=ham_anahtar,
            önek=ham_anahtar[: self.ÖNEK_UZUNLUK],
            sonek=ham_anahtar[-self.SONEK_UZUNLUK :],
            hash=hashlib.sha256(ham_anahtar.encode()).hexdigest(),
        )

    def api_anahtarını_doğrula(self, sağlanan_anahtar: str, saklanan_hash: str) -> bool:
        """Sağlanan bir API anahtarının saklanan hash ile eşleşip eşleşmediğini doğrula."""
        if not sağlanan_anahtar.startswith(self.ÖNEK):
            return False
        return hashlib.sha256(sağlanan_anahtar.encode()).hexdigest() == saklanan_hash
