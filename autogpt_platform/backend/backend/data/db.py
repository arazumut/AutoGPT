import logging
import os
from contextlib import asynccontextmanager
from uuid import uuid4

from dotenv import load_dotenv
from prisma import Prisma
from pydantic import BaseModel, Field, field_validator

from backend.util.retry import conn_retry

# Ortam değişkenlerini yükle
load_dotenv()

# Prisma şema dosyasını al
PRISMA_SCHEMA = os.getenv("PRISMA_SCHEMA", "schema.prisma")
os.environ["PRISMA_SCHEMA_PATH"] = PRISMA_SCHEMA

# Prisma istemcisini oluştur
prisma = Prisma(auto_register=True)

# Logger'ı yapılandır
logger = logging.getLogger(__name__)

# Bağlantı fonksiyonu
@conn_retry("Prisma", "Bağlantı sağlanıyor")
async def connect():
    if prisma.is_connected():
        return

    await prisma.connect()

    if not prisma.is_connected():
        raise ConnectionError("Prisma'ya bağlanılamadı.")

    # Bağlantı havuzundan alınan bağlantı, sorgu bağlantısını reddedebilir.
    try:
        await prisma.execute_raw("SELECT 1")
    except Exception as e:
        raise ConnectionError("Prisma'ya bağlanılamadı.") from e

# Bağlantıyı kesme fonksiyonu
@conn_retry("Prisma", "Bağlantı kesiliyor")
async def disconnect():
    if not prisma.is_connected():
        return

    await prisma.disconnect()

    if prisma.is_connected():
        raise ConnectionError("Prisma bağlantısı kesilemedi.")

# İşlem yönetici fonksiyonu
@asynccontextmanager
async def transaction():
    async with prisma.tx() as tx:
        yield tx

# Temel veritabanı modeli
class BaseDbModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))

    @field_validator("id", mode="before")
    def set_model_id(cls, id: str) -> str:
        # Boş bir ID gönderilirse
        return id or str(uuid4())
