from abc import ABC, abstractmethod
from datetime import datetime, timezone

from prisma import Json
from prisma.enums import CreditTransactionType
from prisma.errors import UniqueViolationError
from prisma.models import CreditTransaction

from backend.data.block import Block, BlockInput, get_block
from backend.data.block_cost_config import BLOCK_COSTS
from backend.data.cost import BlockCost, BlockCostType
from backend.util.settings import Config

config = Config()

class KullaniciKrediTemel(ABC):
    def __init__(self, aylik_kredi_doldurma_miktari: int):
        self.aylik_kredi_doldurma_miktari = aylik_kredi_doldurma_miktari

    @abstractmethod
    async def kredi_al_veya_doldur(self, kullanici_id: str) -> int:
        """
        Kullanıcının mevcut kredisini al ve eğer mevcut döngüde işlem yapılmamışsa doldur.

        Returns:
            int: Kullanıcının mevcut kredisi.
        """
        pass

    @abstractmethod
    async def kredi_harcamak(
        self,
        kullanici_id: str,
        kullanici_kredisi: int,
        blok_id: str,
        girdi_verisi: BlockInput,
        veri_boyutu: float,
        calisma_suresi: float,
    ) -> int:
        """
        Blok kullanımı bazında kullanıcının kredilerini harca.

        Args:
            kullanici_id (str): Kullanıcı ID'si.
            kullanici_kredisi (int): Kullanıcının mevcut kredisi.
            blok_id (str): Blok ID'si.
            girdi_verisi (BlockInput): Blok için girdi verisi.
            veri_boyutu (float): İşlenen verinin boyutu.
            calisma_suresi (float): Blokun çalıştığı süre.

        Returns:
            int: Harcanan kredi miktarı.
        """
        pass

    @abstractmethod
    async def kredi_yukle(self, kullanici_id: str, miktar: int):
        """
        Kullanıcıya kredi yükle.

        Args:
            kullanici_id (str): Kullanıcı ID'si.
            miktar (int): Yüklenecek miktar.
        """
        pass

class KullaniciKredi(KullaniciKrediTemel):
    async def kredi_al_veya_doldur(self, kullanici_id: str) -> int:
        su_an = self.su_an()
        bu_ay = su_an.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        gelecek_ay = (
            bu_ay.replace(month=bu_ay.month + 1)
            if bu_ay.month < 12
            else bu_ay.replace(year=bu_ay.year + 1, month=1)
        )

        kullanici_kredisi = await CreditTransaction.prisma().group_by(
            by=["userId"],
            sum={"amount": True},
            where={
                "userId": kullanici_id,
                "createdAt": {"gte": bu_ay, "lt": gelecek_ay},
                "isActive": True,
            },
        )

        if kullanici_kredisi:
            kredi_toplami = kullanici_kredisi[0].get("_sum") or {}
            return kredi_toplami.get("amount", 0)

        anahtar = f"AYLIK-KREDI-YUKLEME-{bu_ay}"

        try:
            await CreditTransaction.prisma().create(
                data={
                    "amount": self.aylik_kredi_doldurma_miktari,
                    "type": CreditTransactionType.TOP_UP,
                    "userId": kullanici_id,
                    "transactionKey": anahtar,
                    "createdAt": self.su_an(),
                }
            )
        except UniqueViolationError:
            pass  # Bu ay zaten doldurulmuş

        return self.aylik_kredi_doldurma_miktari

    @staticmethod
    def su_an():
        return datetime.now(timezone.utc)

    def _blok_kullanim_maliyeti(
        self,
        blok: Block,
        girdi_verisi: BlockInput,
        veri_boyutu: float,
        calisma_suresi: float,
    ) -> tuple[int, BlockInput]:
        blok_maliyetleri = BLOCK_COSTS.get(type(blok))
        if not blok_maliyetleri:
            return 0, {}

        for blok_maliyeti in blok_maliyetleri:
            if not self._maliyet_filtre_eslesmesi(blok_maliyeti.cost_filter, girdi_verisi):
                continue

            if blok_maliyeti.cost_type == BlockCostType.RUN:
                return blok_maliyeti.cost_amount, blok_maliyeti.cost_filter

            if blok_maliyeti.cost_type == BlockCostType.SECOND:
                return (
                    int(calisma_suresi * blok_maliyeti.cost_amount),
                    blok_maliyeti.cost_filter,
                )

            if blok_maliyeti.cost_type == BlockCostType.BYTE:
                return (
                    int(veri_boyutu * blok_maliyeti.cost_amount),
                    blok_maliyeti.cost_filter,
                )

        return 0, {}

    def _maliyet_filtre_eslesmesi(
        self, maliyet_filtre: BlockInput, girdi_verisi: BlockInput
    ) -> bool:
        """
        Filtre kuralları:
          - Eğer maliyetFiltre bir obje ise, maliyetFiltre'nin girdiVerisi'nin alt kümesi olup olmadığını kontrol et.
          - Aksi takdirde, maliyetFiltre'nin girdiVerisi'ne eşit olup olmadığını kontrol et.
          - Tanımsız, null ve boş string eşit kabul edilir.
        """
        if not isinstance(maliyet_filtre, dict) or not isinstance(girdi_verisi, dict):
            return maliyet_filtre == girdi_verisi

        return all(
            (not girdi_verisi.get(k) and not v)
            or (girdi_verisi.get(k) and self._maliyet_filtre_eslesmesi(v, girdi_verisi[k]))
            for k, v in maliyet_filtre.items()
        )

    async def kredi_harcamak(
        self,
        kullanici_id: str,
        kullanici_kredisi: int,
        blok_id: str,
        girdi_verisi: BlockInput,
        veri_boyutu: float,
        calisma_suresi: float,
        bakiye_dogrulama: bool = True,
    ) -> int:
        blok = get_block(blok_id)
        if not blok:
            raise ValueError(f"Blok bulunamadı: {blok_id}")

        maliyet, eslesen_filtre = self._blok_kullanim_maliyeti(
            blok=blok, girdi_verisi=girdi_verisi, veri_boyutu=veri_boyutu, calisma_suresi=calisma_suresi
        )
        if maliyet <= 0:
            return 0

        if bakiye_dogrulama and kullanici_kredisi < maliyet:
            raise ValueError(f"Yetersiz kredi: {kullanici_kredisi} < {maliyet}")

        await CreditTransaction.prisma().create(
            data={
                "userId": kullanici_id,
                "amount": -maliyet,
                "type": CreditTransactionType.USAGE,
                "blockId": blok.id,
                "metadata": Json(
                    {
                        "block": blok.name,
                        "input": eslesen_filtre,
                    }
                ),
                "createdAt": self.su_an(),
            }
        )
        return maliyet

    async def kredi_yukle(self, kullanici_id: str, miktar: int):
        await CreditTransaction.prisma().create(
            data={
                "userId": kullanici_id,
                "amount": miktar,
                "type": CreditTransactionType.TOP_UP,
                "createdAt": self.su_an(),
            }
        )

class DevreDisiKullaniciKredi(KullaniciKrediTemel):
    async def kredi_al_veya_doldur(self, *args, **kwargs) -> int:
        return 0

    async def kredi_harcamak(self, *args, **kwargs) -> int:
        return 0

    async def kredi_yukle(self, *args, **kwargs):
        pass

def kullanici_kredi_modeli_al() -> KullaniciKrediTemel:
    if config.enable_credit.lower() == "true":
        return KullaniciKredi(config.num_user_credits_refill)
    else:
        return DevreDisiKullaniciKredi(0)

def blok_maliyetlerini_al() -> dict[str, list[BlockCost]]:
    return {blok().id: maliyetler for blok, maliyetler in BLOCK_COSTS.items()}
