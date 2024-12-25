from contextlib import contextmanager
from threading import Lock
from typing import TYPE_CHECKING, Any

from expiringdict import ExpiringDict

if TYPE_CHECKING:
    from redis import Redis
    from redis.lock import Lock as RedisLock


class RedisAnahtarlıMutex:
    """
    Bu sınıf, Redis'i dağıtılmış kilitleme sağlayıcısı olarak kullanarak,
    belirli bir anahtarla kilitlenip açılabilen bir mutex sağlar.
    Anahtar belirli bir süre boyunca açılmazsa bellek sızıntılarını önlemek için
    belirli bir süre sonra mutex'i otomatik olarak temizlemek için ExpiringDict kullanır.
    """

    def __init__(self, redis: "Redis", zaman_asimi: int | None = 60):
        self.redis = redis
        self.zaman_asimi = zaman_asimi
        self.kilitler: dict[Any, "RedisLock"] = ExpiringDict(
            max_len=6000, max_age_seconds=self.zaman_asimi
        )
        self.kilitler_kilidi = Lock()

    @contextmanager
    def kilitli(self, anahtar: Any):
        kilit = self.kilidi_al(anahtar)
        try:
            yield
        finally:
            kilit.release()

    def kilidi_al(self, anahtar: Any) -> "RedisLock":
        """Verilen anahtarla bir kilit alır ve döndürür"""
        with self.kilitler_kilidi:
            if anahtar not in self.kilitler:
                self.kilitler[anahtar] = self.redis.lock(
                    str(anahtar), self.zaman_asimi, thread_local=False
                )
            kilit = self.kilitler[anahtar]
        kilit.acquire()
        return kilit

    def kilidi_birak(self, anahtar: Any):
        if kilit := self.kilitler.get(anahtar):
            kilit.release()

    def tum_kilitleri_birak(self):
        """Tüm kilitlerin serbest bırakıldığından emin olmak için işlem sonlandırıldığında bunu çağırın"""
        self.kilitler_kilidi.acquire(blocking=False)
        for kilit in self.kilitler.values():
            if kilit.locked() and kilit.owned():
                kilit.release()
