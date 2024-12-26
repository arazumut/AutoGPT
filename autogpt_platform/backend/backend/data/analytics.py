import logging
import prisma.types

logger = logging.getLogger(__name__)

# Ham analitik verilerini kaydetmek için fonksiyon
async def ham_analitik_veri_kaydet(
    kullanici_id: str,
    tur: str,
    veri: dict,
    veri_indeksi: str,
):
    detaylar = await prisma.models.AnalyticsDetails.prisma().create(
        data={
            "userId": kullanici_id,
            "type": tur,
            "data": prisma.Json(veri),
            "dataIndex": veri_indeksi,
        }
    )
    return detaylar

# Ham metrik verilerini kaydetmek için fonksiyon
async def ham_metrik_veri_kaydet(
    kullanici_id: str,
    metrik_adi: str,
    metrik_degeri: float,
    veri_stringi: str,
):
    if metrik_degeri < 0:
        raise ValueError("metrik_degeri negatif olamaz")

    sonuc = await prisma.models.AnalyticsMetrics.prisma().create(
        data={
            "value": metrik_degeri,
            "analyticMetric": metrik_adi,
            "userId": kullanici_id,
            "dataString": veri_stringi,
        },
    )

    return sonuc
