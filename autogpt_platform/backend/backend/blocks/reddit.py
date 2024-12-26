from datetime import datetime, timezone
from typing import Iterator

import praw
from pydantic import BaseModel, ConfigDict

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import BlockSecret, SchemaField, SecretField
from backend.util.mock import MockObject


class RedditKimlikBilgileri(BaseModel):
    client_id: BlockSecret = SecretField(key="reddit_client_id")
    client_secret: BlockSecret = SecretField(key="reddit_client_secret")
    username: BlockSecret = SecretField(key="reddit_username")
    password: BlockSecret = SecretField(key="reddit_password")
    user_agent: str = "AutoGPT:1.0 (by /u/autogpt)"

    model_config = ConfigDict(title="Reddit Kimlik Bilgileri")


class RedditGönderisi(BaseModel):
    id: str
    subreddit: str
    başlık: str
    içerik: str


class RedditYorumu(BaseModel):
    gönderi_id: str
    yorum: str


def praw_al(creds: RedditKimlikBilgileri) -> praw.Reddit:
    client = praw.Reddit(
        client_id=creds.client_id.get_secret_value(),
        client_secret=creds.client_secret.get_secret_value(),
        username=creds.username.get_secret_value(),
        password=creds.password.get_secret_value(),
        user_agent=creds.user_agent,
    )
    me = client.user.me()
    if not me:
        raise ValueError("Geçersiz Reddit kimlik bilgileri.")
    print(f"Reddit kullanıcısı olarak giriş yapıldı: {me.name}")
    return client


class RedditGönderileriniAlBlok(Block):
    class Girdi(BlockSchema):
        subreddit: str = SchemaField(description="Subreddit adı")
        creds: RedditKimlikBilgileri = SchemaField(
            description="Reddit kimlik bilgileri",
            default=RedditKimlikBilgileri(),
        )
        son_dakikalar: int | None = SchemaField(
            description="Gönderileri çekerken durulacak dakika",
            default=None,
        )
        son_gönderi: str | None = SchemaField(
            description="Gönderileri çekerken ulaşıldığında durulacak gönderi ID'si",
            default=None,
        )
        gönderi_limiti: int | None = SchemaField(
            description="Çekilecek gönderi sayısı", default=10
        )

    class Çıktı(BlockSchema):
        gönderi: RedditGönderisi = SchemaField(description="Reddit gönderisi")

    def __init__(self):
        super().__init__(
            disabled=True,
            id="c6731acb-4285-4ee1-bc9b-03d0766c370f",
            description="Bu blok, tanımlı bir subreddit adından Reddit gönderilerini çeker.",
            categories={BlockCategory.SOCIAL},
            input_schema=RedditGönderileriniAlBlok.Girdi,
            output_schema=RedditGönderileriniAlBlok.Çıktı,
            test_input={
                "creds": {
                    "client_id": "client_id",
                    "client_secret": "client_secret",
                    "username": "username",
                    "password": "password",
                    "user_agent": "user_agent",
                },
                "subreddit": "subreddit",
                "son_gönderi": "id3",
                "gönderi_limiti": 2,
            },
            test_output=[
                (
                    "gönderi",
                    RedditGönderisi(
                        id="id1", subreddit="subreddit", başlık="başlık1", içerik="içerik1"
                    ),
                ),
                (
                    "gönderi",
                    RedditGönderisi(
                        id="id2", subreddit="subreddit", başlık="başlık2", içerik="içerik2"
                    ),
                ),
            ],
            test_mock={
                "get_posts": lambda _: [
                    MockObject(id="id1", title="başlık1", selftext="içerik1"),
                    MockObject(id="id2", title="başlık2", selftext="içerik2"),
                    MockObject(id="id3", title="başlık2", selftext="içerik2"),
                ]
            },
        )

    @staticmethod
    def gönderileri_al(girdi_verisi: Girdi) -> Iterator[praw.reddit.Submission]:
        client = praw_al(girdi_verisi.creds)
        subreddit = client.subreddit(girdi_verisi.subreddit)
        return subreddit.new(limit=girdi_verisi.gönderi_limiti or 10)

    def çalıştır(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        current_time = datetime.now(tz=timezone.utc)
        for gönderi in self.gönderileri_al(girdi_verisi):
            if girdi_verisi.son_dakikalar:
                gönderi_zamanı = datetime.fromtimestamp(
                    gönderi.created_utc, tz=timezone.utc
                )
                zaman_farkı = current_time - gönderi_zamanı
                if zaman_farkı.total_seconds() / 60 > girdi_verisi.son_dakikalar:
                    continue

            if girdi_verisi.son_gönderi and gönderi.id == girdi_verisi.son_gönderi:
                break

            yield "gönderi", RedditGönderisi(
                id=gönderi.id,
                subreddit=girdi_verisi.subreddit,
                başlık=gönderi.title,
                içerik=gönderi.selftext,
            )


class RedditYorumuGönderBlok(Block):
    class Girdi(BlockSchema):
        creds: RedditKimlikBilgileri = SchemaField(
            description="Reddit kimlik bilgileri", default=RedditKimlikBilgileri()
        )
        veri: RedditYorumu = SchemaField(description="Reddit yorumu")

    class Çıktı(BlockSchema):
        yorum_id: str = SchemaField(description="Gönderilen yorum ID'si")

    def __init__(self):
        super().__init__(
            id="4a92261b-701e-4ffb-8970-675fd28e261f",
            description="Bu blok, belirtilen bir Reddit gönderisine yorum yapar.",
            categories={BlockCategory.SOCIAL},
            input_schema=RedditYorumuGönderBlok.Girdi,
            output_schema=RedditYorumuGönderBlok.Çıktı,
            test_input={"veri": {"gönderi_id": "id", "yorum": "yorum"}},
            test_output=[("yorum_id", "dummy_comment_id")],
            test_mock={"reply_post": lambda creds, comment: "dummy_comment_id"},
        )

    @staticmethod
    def gönderiye_yorum_yap(creds: RedditKimlikBilgileri, yorum: RedditYorumu) -> str:
        client = praw_al(creds)
        submission = client.submission(id=yorum.gönderi_id)
        yeni_yorum = submission.reply(yorum.yorum)
        if not yeni_yorum:
            raise ValueError("Yorum gönderilemedi.")
        return yeni_yorum.id

    def çalıştır(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        yield "yorum_id", self.gönderiye_yorum_yap(girdi_verisi.creds, girdi_verisi.veri)
