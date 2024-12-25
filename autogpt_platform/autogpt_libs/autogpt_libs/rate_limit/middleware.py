from fastapi import HTTPException, Request
from starlette.middleware.base import RequestResponseEndpoint

from .limiter import RateLimiter


async def oran_sınırı_ara_katmanı(request: Request, call_next: RequestResponseEndpoint):
    """API istekleri için oran sınırlama ara katmanı."""
    sınırlayıcı = RateLimiter()

    if not request.url.path.startswith("/api"):
        return await call_next(request)

    api_anahtarı = request.headers.get("Authorization")
    if not api_anahtarı:
        return await call_next(request)

    api_anahtarı = api_anahtarı.replace("Bearer ", "")

    izin_verildi_mi, kalan, sıfırlama_zamanı = await sınırlayıcı.oran_sınırını_kontrol_et(api_anahtarı)

    if not izin_verildi_mi:
        raise HTTPException(
            status_code=429, detail="Oran sınırı aşıldı. Lütfen daha sonra tekrar deneyin."
        )

    yanıt = await call_next(request)
    yanıt.headers["X-RateLimit-Limit"] = str(sınırlayıcı.max_requests)
    yanıt.headers["X-RateLimit-Remaining"] = str(kalan)
    yanıt.headers["X-RateLimit-Reset"] = str(sıfırlama_zamanı)

    return yanıt
