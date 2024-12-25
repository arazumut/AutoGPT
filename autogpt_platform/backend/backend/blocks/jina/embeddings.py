from backend.blocks.jina._auth import (
    JinaKimlikBilgileri,
    JinaKimlikBilgileriAlanı,
    JinaKimlikBilgileriGirişi,
)
from backend.data.block import Blok, BlokKategori, BlokÇıktısı, BlokŞeması
from backend.data.model import ŞemaAlanı
from backend.util.request import istekler


class JinaGömmeBloku(Blok):
    class Giriş(BlokŞeması):
        metinler: list = ŞemaAlanı(açıklama="Gömülecek metinlerin listesi")
        kimlik_bilgileri: JinaKimlikBilgileriGirişi = JinaKimlikBilgileriAlanı()
        model: str = ŞemaAlanı(
            açıklama="Kullanılacak Jina gömme modeli",
            varsayılan="jina-embeddings-v2-base-en",
        )

    class Çıkış(BlokŞeması):
        gömmeler: list = ŞemaAlanı(açıklama="Gömme listesi")

    def __init__(self):
        super().__init__(
            id="7c56b3ab-62e7-43a2-a2dc-4ec4245660b6",
            açıklama="Jina AI kullanarak gömmeler oluşturur",
            kategoriler={BlokKategori.YZ},
            giriş_şeması=JinaGömmeBloku.Giriş,
            çıkış_şeması=JinaGömmeBloku.Çıkış,
        )

    def çalıştır(
        self, giriş_verisi: Giriş, *, kimlik_bilgileri: JinaKimlikBilgileri, **kwargs
    ) -> BlokÇıktısı:
        url = "https://api.jina.ai/v1/embeddings"
        başlıklar = {
            "İçerik-Tipi": "application/json",
            "Yetkilendirme": f"Bearer {kimlik_bilgileri.api_anahtarı.get_secret_value()}",
        }
        veri = {"giriş": giriş_verisi.metinler, "model": giriş_verisi.model}
        yanıt = istekler.post(url, başlıklar=başlıklar, json=veri)
        gömmeler = [e["gömme"] for e in yanıt.json()["veri"]]
        yield "gömmeler", gömmeler
