from enum import Enum
from typing import List, Literal

from pydantic import SecretStr

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    APIKeyCredentials,
    BlockSecret,
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
    SecretField,
)
from backend.integrations.providers import ProviderName
from backend.util.request import requests

# Test için kullanılan API anahtar bilgileri
TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="medium",
    api_key=SecretStr("mock-medium-api-key"),
    title="Mock Medium API key",
    expires_at=None,
)
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.type,
}

# Yayın durumu seçenekleri
class PublishToMediumStatus(str, Enum):
    PUBLIC = "public"
    DRAFT = "draft"
    UNLISTED = "unlisted"

# Medium'a gönderi yayınlama bloğu
class PublishToMediumBlock(Block):
    class Input(BlockSchema):
        author_id: BlockSecret = SecretField(
            key="medium_author_id",
            description="""Kullanıcının Medium AuthorID'si. Bunu Medium API'sinin /me endpoint'ini çağırarak alabilirsiniz.\n\ncurl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" https://api.medium.com/v1/me" yanıtında authorId alanı bulunacaktır.""",
            placeholder="Yazarın Medium AuthorID'sini girin",
        )
        title: str = SchemaField(
            description="Medium gönderinizin başlığı",
            placeholder="Gönderi başlığınızı girin",
        )
        content: str = SchemaField(
            description="Medium gönderinizin ana içeriği",
            placeholder="Gönderi içeriğinizi girin",
        )
        content_format: str = SchemaField(
            description="İçeriğin formatı: 'html' veya 'markdown'",
            placeholder="html",
        )
        tags: List[str] = SchemaField(
            description="Medium gönderiniz için etiket listesi (en fazla 5)",
            placeholder="['teknoloji', 'AI', 'blog']",
        )
        canonical_url: str | None = SchemaField(
            default=None,
            description="Bu içeriğin orijinal olarak yayınlandığı yer, eğer başka bir yerde yayınlandıysa",
            placeholder="https://yourblog.com/original-post",
        )
        publish_status: PublishToMediumStatus = SchemaField(
            description="Yayın durumu",
            placeholder=PublishToMediumStatus.DRAFT,
        )
        license: str = SchemaField(
            default="all-rights-reserved",
            description="Gönderinin lisansı: 'all-rights-reserved', 'cc-40-by', 'cc-40-by-sa', 'cc-40-by-nd', 'cc-40-by-nc', 'cc-40-by-nc-nd', 'cc-40-by-nc-sa', 'cc-40-zero', 'public-domain'",
            placeholder="all-rights-reserved",
        )
        notify_followers: bool = SchemaField(
            default=False,
            description="Kullanıcının takipçilerine yayınlandığını bildirip bildirmeyeceği",
            placeholder="False",
        )
        credentials: CredentialsMetaInput[
            Literal[ProviderName.MEDIUM], Literal["api_key"]
        ] = CredentialsField(
            description="Medium entegrasyonu, yeterli izinlere sahip herhangi bir API anahtarı ile kullanılabilir.",
        )

    class Output(BlockSchema):
        post_id: str = SchemaField(description="Oluşturulan Medium gönderisinin ID'si")
        post_url: str = SchemaField(description="Oluşturulan Medium gönderisinin URL'si")
        published_at: int = SchemaField(
            description="Gönderinin yayınlandığı zamanın zaman damgası"
        )
        error: str = SchemaField(
            description="Gönderi oluşturma başarısız olursa hata mesajı"
        )

    def __init__(self):
        super().__init__(
            id="3f7b2dcb-4a78-4e3f-b0f1-88132e1b89df",
            input_schema=PublishToMediumBlock.Input,
            output_schema=PublishToMediumBlock.Output,
            description="Medium'a bir gönderi yayınlar.",
            categories={BlockCategory.SOCIAL},
            test_input={
                "author_id": "1234567890abcdef",
                "title": "Test Gönderisi",
                "content": "<h1>Test İçeriği</h1><p>Bu bir test gönderisidir.</p>",
                "content_format": "html",
                "tags": ["test", "otomasyon"],
                "license": "all-rights-reserved",
                "notify_followers": False,
                "publish_status": PublishToMediumStatus.DRAFT.value,
                "credentials": TEST_CREDENTIALS_INPUT,
            },
            test_output=[
                ("post_id", "e6f36a"),
                ("post_url", "https://medium.com/@username/test-post-e6f36a"),
                ("published_at", 1626282600),
            ],
            test_mock={
                "create_post": lambda *args, **kwargs: {
                    "data": {
                        "id": "e6f36a",
                        "url": "https://medium.com/@username/test-post-e6f36a",
                        "authorId": "1234567890abcdef",
                        "publishedAt": 1626282600,
                    }
                }
            },
            test_credentials=TEST_CREDENTIALS,
        )

    def create_post(
        self,
        api_key: SecretStr,
        author_id,
        title,
        content,
        content_format,
        tags,
        canonical_url,
        publish_status,
        license,
        notify_followers,
    ):
        headers = {
            "Authorization": f"Bearer {api_key.get_secret_value()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        data = {
            "title": title,
            "content": content,
            "contentFormat": content_format,
            "tags": tags,
            "canonicalUrl": canonical_url,
            "publishStatus": publish_status,
            "license": license,
            "notifyFollowers": notify_followers,
        }

        response = requests.post(
            f"https://api.medium.com/v1/users/{author_id}/posts",
            headers=headers,
            json=data,
        )

        return response.json()

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        response = self.create_post(
            credentials.api_key,
            input_data.author_id.get_secret_value(),
            input_data.title,
            input_data.content,
            input_data.content_format,
            input_data.tags,
            input_data.canonical_url,
            input_data.publish_status,
            input_data.license,
            input_data.notify_followers,
        )

        if "data" in response:
            yield "post_id", response["data"]["id"]
            yield "post_url", response["data"]["url"]
            yield "published_at", response["data"]["publishedAt"]
        else:
            error_message = response.get("errors", [{}])[0].get(
                "message", "Bilinmeyen bir hata oluştu"
            )
            raise RuntimeError(f"Medium gönderisi oluşturulamadı: {error_message}")
