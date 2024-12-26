import logging
import os

from dotenv import load_dotenv
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from backend.util.retry import conn_retry

# .env dosyasını yükle
load_dotenv()

# Ortam değişkenlerinden Redis bağlantı bilgilerini al
HOST = os.getenv("REDIS_HOST", "localhost")
PORT = int(os.getenv("REDIS_PORT", "6379"))
PASSWORD = os.getenv("REDIS_PASSWORD", "password")

# Logger oluştur
logger = logging.getLogger(__name__)
connection: Redis | None = None
connection_async: AsyncRedis | None = None

# Redis bağlantısı kurma fonksiyonu
@conn_retry("Redis", "Bağlantı kuruluyor")
def connect() -> Redis:
    global connection
    if connection:
        return connection

    c = Redis(
        host=HOST,
        port=PORT,
        password=PASSWORD,
        decode_responses=True,
    )
    c.ping()
    connection = c
    return connection

# Redis bağlantısını kapatma fonksiyonu
@conn_retry("Redis", "Bağlantı kapatılıyor")
def disconnect():
    global connection
    if connection:
        connection.close()
    connection = None

# Redis bağlantısını alma fonksiyonu
def get_redis(auto_connect: bool = True) -> Redis:
    if connection:
        return connection
    if auto_connect:
        return connect()
    raise RuntimeError("Redis bağlantısı kurulamadı")

# Asenkron Redis bağlantısı kurma fonksiyonu
@conn_retry("AsyncRedis", "Bağlantı kuruluyor")
async def connect_async() -> AsyncRedis:
    global connection_async
    if connection_async:
        return connection_async

    c = AsyncRedis(
        host=HOST,
        port=PORT,
        password=PASSWORD,
        decode_responses=True,
    )
    await c.ping()
    connection_async = c
    return connection_async

# Asenkron Redis bağlantısını kapatma fonksiyonu
@conn_retry("AsyncRedis", "Bağlantı kapatılıyor")
async def disconnect_async():
    global connection_async
    if connection_async:
        await connection_async.close()
    connection_async = None

# Asenkron Redis bağlantısını alma fonksiyonu
async def get_redis_async(auto_connect: bool = True) -> AsyncRedis:
    if connection_async:
        return connection_async
    if auto_connect:
        return await connect_async()
    raise RuntimeError("AsyncRedis bağlantısı kurulamadı")
