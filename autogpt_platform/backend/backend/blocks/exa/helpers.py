from typing import Optional
from pydantic import BaseModel

from backend.data.model import SchemaField

class MetinAyarları(BaseModel):
    maksimum_karakter: int = SchemaField(
        default=1000,
        description="Döndürülecek maksimum karakter sayısı",
        placeholder="1000",
    )
    html_etiketlerini_dahil_et: bool = SchemaField(
        default=False,
        description="Metinde HTML etiketlerini dahil edip etmeme",
        placeholder="False",
    )

class VurguAyarları(BaseModel):
    cümle_sayısı: int = SchemaField(
        default=3,
        description="Her vurgu için cümle sayısı",
        placeholder="3",
    )
    url_başına_vurgu: int = SchemaField(
        default=3,
        description="URL başına vurgu sayısı",
        placeholder="3",
    )

class ÖzetAyarları(BaseModel):
    sorgu: Optional[str] = SchemaField(
        default="",
        description="Özetleme için sorgu dizesi",
        placeholder="Sorgu girin",
    )

class İçerikAyarları(BaseModel):
    metin: MetinAyarları = SchemaField(
        default=MetinAyarları(),
        description="Metin içerik ayarları",
    )
    vurgular: VurguAyarları = SchemaField(
        default=VurguAyarları(),
        description="Vurgu ayarları",
    )
    özet: ÖzetAyarları = SchemaField(
        default=ÖzetAyarları(),
        description="Özet ayarları",
    )
