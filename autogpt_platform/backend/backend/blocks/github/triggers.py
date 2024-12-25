import json
import logging
from pathlib import Path

from pydantic import BaseModel

from backend.data.block import (
    Block,
    BlockCategory,
    BlockOutput,
    BlockSchema,
    BlockWebhookConfig,
)
from backend.data.model import SchemaField

from ._auth import (
    TEST_CREDENTIALS,
    TEST_CREDENTIALS_INPUT,
    GithubCredentialsField,
    GithubCredentialsInput,
)

logger = logging.getLogger(__name__)


# --8<-- [start:GithubTriggerExample]
class GitHubTetikleyiciTemel:
    class Girdi(BlockSchema):
        kimlik_bilgileri: GithubCredentialsInput = GithubCredentialsField("repo")
        repo: str = SchemaField(
            description=(
                "Abone olunacak depo.\n\n"
                "**Not:** GitHub kimlik bilgilerinizin bu depoda webhook oluşturma "
                "izinlerine sahip olduğundan emin olun."
            ),
            placeholder="{owner}/{repo}",
        )
        # --8<-- [start:example-payload-field]
        yük: dict = SchemaField(gizli=True, varsayılan={})
        # --8<-- [end:example-payload-field]

    class Çıktı(BlockSchema):
        yük: dict = SchemaField(
            description="GitHub'dan alınan tam webhook yükü. "
            "Etkilenen kaynak (ör. çekme isteği), olay ve olayı tetikleyen kullanıcı hakkında bilgi içerir."
        )
        tetikleyen_kullanıcı: dict = SchemaField(
            description="Olayı tetikleyen GitHub kullanıcısını temsil eden nesne"
        )
        hata: str = SchemaField(
            description="Yük işlenemediğinde hata mesajı"
        )

    def çalıştır(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        yield "yük", girdi_verisi.yük
        yield "tetikleyen_kullanıcı", girdi_verisi.yük["gönderen"]


class GithubÇekmeİsteğiTetikleyiciBlok(GitHubTetikleyiciTemel, Block):
    ÖRNEK_YÜK_DOSYASI = (
        Path(__file__).parent / "örnek_yükler" / "çekme_isteği.synchronize.json"
    )

    # --8<-- [start:example-event-filter]
    class Girdi(GitHubTetikleyiciTemel.Girdi):
        class OlaylarFiltresi(BaseModel):
            """
            https://docs.github.com/en/webhooks/webhook-events-and-payloads#pull_request
            """

            açıldı: bool = False
            düzenlendi: bool = False
            kapandı: bool = False
            yeniden_açıldı: bool = False
            senkronize: bool = False
            atandı: bool = False
            atanmadı: bool = False
            etiketlendi: bool = False
            etiketlenmedi: bool = False
            taslağa_dönüştürüldü: bool = False
            kilitlendi: bool = False
            kilit_açıldı: bool = False
            sıraya_alındı: bool = False
            sıradan_çıkarıldı: bool = False
            kilometre_taşı_eklendi: bool = False
            kilometre_taşı_kaldırıldı: bool = False
            inceleme_için_hazır: bool = False
            inceleme_istendi: bool = False
            inceleme_isteği_kaldırıldı: bool = False
            otomatik_birleştirme_etkinleştirildi: bool = False
            otomatik_birleştirme_devre_dışı_bırakıldı: bool = False

        olaylar: OlaylarFiltresi = SchemaField(
            title="Olaylar", description="Abone olunacak olaylar"
        )
        # --8<-- [end:example-event-filter]

    class Çıktı(GitHubTetikleyiciTemel.Çıktı):
        olay: str = SchemaField(
            description="Webhook'u tetikleyen PR olayı (ör. 'açıldı')"
        )
        numara: int = SchemaField(description="Etkilenen çekme isteğinin numarası")
        çekme_isteği: dict = SchemaField(
            description="Etkilenen çekme isteğini temsil eden nesne"
        )
        çekme_isteği_url: str = SchemaField(
            description="Etkilenen çekme isteğinin URL'si"
        )

    def __init__(self):
        from backend.integrations.webhooks.github import GithubWebhookType

        örnek_yük = json.loads(
            self.ÖRNEK_YÜK_DOSYASI.read_text(encoding="utf-8")
        )

        super().__init__(
            id="6c60ec01-8128-419e-988f-96a063ee2fea",
            description="Bu blok çekme isteği olaylarında tetiklenir ve olay türünü ve yükü çıktılar.",
            categories={BlockCategory.DEVELOPER_TOOLS, BlockCategory.INPUT},
            input_schema=GithubÇekmeİsteğiTetikleyiciBlok.Girdi,
            output_schema=GithubÇekmeİsteğiTetikleyiciBlok.Çıktı,
            # --8<-- [start:example-webhook_config]
            webhook_config=BlockWebhookConfig(
                provider="github",
                webhook_type=GithubWebhookType.REPO,
                resource_format="{repo}",
                event_filter_input="olaylar",
                event_format="çekme_isteği.{olay}",
            ),
            # --8<-- [end:example-webhook_config]
            test_input={
                "repo": "Significant-Gravitas/AutoGPT",
                "olaylar": {"açıldı": True, "senkronize": True},
                "kimlik_bilgileri": TEST_CREDENTIALS_INPUT,
                "yük": örnek_yük,
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=[
                ("yük", örnek_yük),
                ("tetikleyen_kullanıcı", örnek_yük["gönderen"]),
                ("olay", örnek_yük["eylem"]),
                ("numara", örnek_yük["numara"]),
                ("çekme_isteği", örnek_yük["çekme_isteği"]),
                ("çekme_isteği_url", örnek_yük["çekme_isteği"]["html_url"]),
            ],
        )

    def çalıştır(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:  # type: ignore
        yield from super().çalıştır(girdi_verisi, **kwargs)
        yield "olay", girdi_verisi.yük["eylem"]
        yield "numara", girdi_verisi.yük["numara"]
        yield "çekme_isteği", girdi_verisi.yük["çekme_isteği"]
        yield "çekme_isteği_url", girdi_verisi.yük["çekme_isteği"]["html_url"]


# --8<-- [end:GithubTriggerExample]
