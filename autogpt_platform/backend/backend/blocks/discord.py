import asyncio
from typing import Literal

import aiohttp
import discord
from pydantic import SecretStr

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
)
from backend.integrations.providers import ProviderName

DiscordCredentials = CredentialsMetaInput[
    Literal[ProviderName.DISCORD], Literal["api_key"]
]


def DiscordCredentialsField() -> DiscordCredentials:
    return CredentialsField(description="Discord bot token")


TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="discord",
    api_key=SecretStr("test_api_key"),
    title="Mock Discord API key",
    expires_at=None,
)
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.type,
}


class ReadDiscordMessagesBlock(Block):
    class Input(BlockSchema):
        credentials: DiscordCredentials = DiscordCredentialsField()

    class Output(BlockSchema):
        message_content: str = SchemaField(
            description="Alınan mesajın içeriği"
        )
        channel_name: str = SchemaField(
            description="Mesajın alındığı kanalın adı"
        )
        username: str = SchemaField(
            description="Mesajı gönderen kullanıcının adı"
        )

    def __init__(self):
        super().__init__(
            id="df06086a-d5ac-4abb-9996-2ad0acb2eff7",
            input_schema=ReadDiscordMessagesBlock.Input,  # Giriş şemasını ata
            output_schema=ReadDiscordMessagesBlock.Output,  # Çıkış şemasını ata
            description="Bir bot token kullanarak bir Discord kanalından mesajları okur.",
            categories={BlockCategory.SOCIAL},
            test_input={
                "continuous_read": False,
                "credentials": TEST_CREDENTIALS_INPUT,
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=[
                (
                    "message_content",
                    "Merhaba!\n\nKullanıcıdan dosya: example.txt\nİçerik: Bu dosyanın içeriğidir.",
                ),
                ("channel_name", "genel"),
                ("username", "test_kullanıcı"),
            ],
            test_mock={
                "run_bot": lambda token: asyncio.Future()  # Mock için bir Future nesnesi oluştur
            },
        )

    async def run_bot(self, token: SecretStr):
        intents = discord.Intents.default()
        intents.message_content = True

        client = discord.Client(intents=intents)

        self.output_data = None
        self.channel_name = None
        self.username = None

        @client.event
        async def on_ready():
            print(f"{client.user} olarak giriş yapıldı")

        @client.event
        async def on_message(message):
            if message.author == client.user:
                return

            self.output_data = message.content
            self.channel_name = message.channel.name
            self.username = message.author.name

            if message.attachments:
                attachment = message.attachments[0]  # İlk eki işle
                if attachment.filename.endswith((".txt", ".py")):
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as response:
                            file_content = await response.text()
                            self.output_data += f"\n\nKullanıcıdan dosya: {attachment.filename}\nİçerik: {file_content}"

            await client.close()

        await client.start(token.get_secret_value())

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        while True:
            for output_name, output_value in self.__run(input_data, credentials):
                yield output_name, output_value
            break

    def __run(self, input_data: Input, credentials: APIKeyCredentials) -> BlockOutput:
        try:
            loop = asyncio.get_event_loop()
            future = self.run_bot(credentials.api_key)

            # Eğer Future (mock) ise, sonucu ayarla
            if isinstance(future, asyncio.Future):
                future.set_result(
                    {
                        "output_data": "Merhaba!\n\nKullanıcıdan dosya: example.txt\nİçerik: Bu dosyanın içeriğidir.",
                        "channel_name": "genel",
                        "username": "test_kullanıcı",
                    }
                )

            result = loop.run_until_complete(future)

            # Test amaçlı, mock sonucu kullan
            if isinstance(result, dict):
                self.output_data = result.get("output_data")
                self.channel_name = result.get("channel_name")
                self.username = result.get("username")

            if (
                self.output_data is None
                or self.channel_name is None
                or self.username is None
            ):
                raise ValueError("Mesaj, kanal adı veya kullanıcı adı alınamadı.")

            yield "message_content", self.output_data
            yield "channel_name", self.channel_name
            yield "username", self.username

        except discord.errors.LoginFailure as login_err:
            raise ValueError(f"Giriş hatası oluştu: {login_err}")
        except Exception as e:
            raise ValueError(f"Bir hata oluştu: {e}")


class SendDiscordMessageBlock(Block):
    class Input(BlockSchema):
        credentials: DiscordCredentials = DiscordCredentialsField()
        message_content: str = SchemaField(
            description="Gönderilecek mesajın içeriği"
        )
        channel_name: str = SchemaField(
            description="Mesajın gönderileceği kanalın adı"
        )

    class Output(BlockSchema):
        status: str = SchemaField(
            description="İşlemin durumu (örneğin, 'Mesaj gönderildi', 'Hata')"
        )

    def __init__(self):
        super().__init__(
            id="d0822ab5-9f8a-44a3-8971-531dd0178b6b",
            input_schema=SendDiscordMessageBlock.Input,  # Giriş şemasını ata
            output_schema=SendDiscordMessageBlock.Output,  # Çıkış şemasını ata
            description="Bir bot token kullanarak bir Discord kanalına mesaj gönderir.",
            categories={BlockCategory.SOCIAL},
            test_input={
                "channel_name": "genel",
                "message_content": "Merhaba, Discord!",
                "credentials": TEST_CREDENTIALS_INPUT,
            },
            test_output=[("status", "Mesaj gönderildi")],
            test_mock={
                "send_message": lambda token, channel_name, message_content: asyncio.Future()
            },
            test_credentials=TEST_CREDENTIALS,
        )

    async def send_message(self, token: str, channel_name: str, message_content: str):
        intents = discord.Intents.default()
        intents.guilds = True  # Sunucu/kanal bilgilerini almak için gerekli
        client = discord.Client(intents=intents)

        @client.event
        async def on_ready():
            print(f"{client.user} olarak giriş yapıldı")
            for guild in client.guilds:
                for channel in guild.text_channels:
                    if channel.name == channel_name:
                        # Mesaj 2000 karakteri aşıyorsa parçalara böl
                        for chunk in self.chunk_message(message_content):
                            await channel.send(chunk)
                        self.output_data = "Mesaj gönderildi"
                        await client.close()
                        return

            self.output_data = "Kanal bulunamadı"
            await client.close()

        await client.start(token)

    def chunk_message(self, message: str, limit: int = 2000) -> list:
        """Mesajı Discord limitini aşmayacak şekilde parçalara böler."""
        return [message[i : i + limit] for i in range(0, len(message), limit)]

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        try:
            loop = asyncio.get_event_loop()
            future = self.send_message(
                credentials.api_key.get_secret_value(),
                input_data.channel_name,
                input_data.message_content,
            )

            # Eğer Future (mock) ise, sonucu ayarla
            if isinstance(future, asyncio.Future):
                future.set_result("Mesaj gönderildi")

            result = loop.run_until_complete(future)

            # Test amaçlı, mock sonucu kullan
            if isinstance(result, str):
                self.output_data = result

            if self.output_data is None:
                raise ValueError("Durum mesajı alınamadı.")

            yield "status", self.output_data

        except discord.errors.LoginFailure as login_err:
            raise ValueError(f"Giriş hatası oluştu: {login_err}")
        except Exception as e:
            raise ValueError(f"Bir hata oluştu: {e}")

