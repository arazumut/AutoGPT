import time
from typing import Tuple

from redis import Redis

from .config import RATE_LIMIT_SETTINGS


class OranSınırlayıcı:
    def __init__(
        self,
        redis_host: str = RATE_LIMIT_SETTINGS.redis_host,
        redis_port: str = RATE_LIMIT_SETTINGS.redis_port,
        redis_password: str = RATE_LIMIT_SETTINGS.redis_password,
        dakika_başına_istek: int = RATE_LIMIT_SETTINGS.requests_per_minute,
    ):
        self.redis = Redis(
            host=redis_host,
            port=int(redis_port),
            password=redis_password,
            decode_responses=True,
        )
        self.pencere = 60
        self.max_istek = dakika_başına_istek

    async def oran_sınırını_kontrol_et(self, api_anahtarı_id: str) -> Tuple[bool, int, int]:
        """
        İsteğin oran sınırları içinde olup olmadığını kontrol et.

        Args:
            api_anahtarı_id: Kontrol edilecek API anahtarı kimliği

        Returns:
            (izin_verildi, kalan_istek, sıfırlama_zamanı) şeklinde bir demet
        """
        şimdi = time.time()
        pencere_başlangıcı = şimdi - self.pencere
        anahtar = f"oransınırı:{api_anahtarı_id}:1dakika"

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(anahtar, 0, pencere_başlangıcı)
        pipe.zadd(anahtar, {str(şimdi): şimdi})
        pipe.zcount(anahtar, pencere_başlangıcı, şimdi)
        pipe.expire(anahtar, self.pencere)

        _, _, istek_sayısı, _ = pipe.execute()

        kalan = max(0, self.max_istek - istek_sayısı)
        sıfırlama_zamanı = int(şimdi + self.pencere)

        return istek_sayısı <= self.max_istek, kalan, sıfırlama_zamanı
