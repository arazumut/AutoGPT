from enum import Enum
from typing import Literal

from e2b_code_interpreter import Sandbox
from pydantic import SecretStr

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import (
    APIKeyCredentials,
    CredentialsField,
    CredentialsMetaInput,
    SchemaField,
)
from backend.integrations.providers import ProviderName

# Test için kullanılan API anahtar bilgileri
TEST_CREDENTIALS = APIKeyCredentials(
    id="01234567-89ab-cdef-0123-456789abcdef",
    provider="e2b",
    api_key=SecretStr("mock-e2b-api-key"),
    title="Mock E2B API key",
    expires_at=None,
)
TEST_CREDENTIALS_INPUT = {
    "provider": TEST_CREDENTIALS.provider,
    "id": TEST_CREDENTIALS.id,
    "type": TEST_CREDENTIALS.type,
    "title": TEST_CREDENTIALS.type,
}

# Desteklenen programlama dilleri
class ProgramlamaDili(Enum):
    PYTHON = "python"
    JAVASCRIPT = "js"
    BASH = "bash"
    R = "r"
    JAVA = "java"

# Kod yürütme bloğu
class KodYurutmeBlogu(Block):
    # TODO : Dosya yükleme ve indirme desteği ekle
    # Şu anda, CPU ve Belleği yalnızca önceden özelleştirilmiş bir sandbox şablonu oluşturarak özelleştirebilirsiniz
    class Girdi(BlockSchema):
        kimlik_bilgileri: CredentialsMetaInput[
            Literal[ProviderName.E2B], Literal["api_key"]
        ] = CredentialsField(
            description="E2B Sandbox için API anahtarınızı girin. Buradan alabilirsiniz - https://e2b.dev/docs",
        )

        # TODO : Komutları arka planda çalıştırma seçeneği ekle
        kurulum_komutlari: list[str] = SchemaField(
            description=(
                "Sandbox'u kodu çalıştırmadan önce ayarlamak için kabuk komutları. "
                "İstediğiniz Debian tabanlı paket yöneticisini kurmak için `curl` veya `git` kullanabilirsiniz. "
                "`pip` ve `npm` önceden yüklenmiştir.\n\n"
                "Bu komutlar `sh` ile ön planda çalıştırılır."
            ),
            placeholder="pip install cowsay",
            default=[],
            advanced=False,
        )

        kod: str = SchemaField(
            description="Sandbox içinde çalıştırılacak kod",
            placeholder="print('Merhaba, Dünya!')",
            default="",
            advanced=False,
        )

        dil: ProgramlamaDili = SchemaField(
            description="Çalıştırılacak programlama dili",
            default=ProgramlamaDili.PYTHON,
            advanced=False,
        )

        zaman_asimi: int = SchemaField(
            description="Çalıştırma zaman aşımı süresi (saniye cinsinden)", default=300
        )

        sablon_id: str = SchemaField(
            description=(
                "Bir E2B sandbox şablonu kullanabilirsiniz, bunun için buraya ID'sini girin. "
                "Daha fazla detay için E2B dokümanlarına bakın: "
                "[E2B - Sandbox template](https://e2b.dev/docs/sandbox-template)"
            ),
            default="",
            advanced=True,
        )

    class Cikti(BlockSchema):
        yanit: str = SchemaField(description="Kod yürütme yanıtı")
        stdout_loglari: str = SchemaField(
            description="Çalıştırma sırasında standart çıktı logları"
        )
        stderr_loglari: str = SchemaField(description="Çalıştırma sırasında standart hata logları")
        hata: str = SchemaField(description="Çalıştırma başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="0b02b072-abe7-11ef-8372-fb5d162dd712",
            description="İnternet erişimi olan izole bir sandbox ortamında kod çalıştırır.",
            categories={BlockCategory.DEVELOPER_TOOLS},
            input_schema=KodYurutmeBlogu.Girdi,
            output_schema=KodYurutmeBlogu.Cikti,
            test_credentials=TEST_CREDENTIALS,
            test_input={
                "kimlik_bilgileri": TEST_CREDENTIALS_INPUT,
                "kod": "print('Merhaba Dünya')",
                "dil": ProgramlamaDili.PYTHON.value,
                "kurulum_komutlari": [],
                "zaman_asimi": 300,
                "sablon_id": "",
            },
            test_output=[
                ("yanit", "Merhaba Dünya"),
                ("stdout_loglari", "Merhaba Dünya\n"),
            ],
            test_mock={
                "kod_yurut": lambda kod, dil, kurulum_komutlari, zaman_asimi, api_key, sablon_id: (
                    "Merhaba Dünya",
                    "Merhaba Dünya\n",
                    "",
                ),
            },
        )

    def kod_yurut(
        self,
        kod: str,
        dil: ProgramlamaDili,
        kurulum_komutlari: list[str],
        zaman_asimi: int,
        api_key: str,
        sablon_id: str,
    ):
        try:
            sandbox = None
            if sablon_id:
                sandbox = Sandbox(
                    template=sablon_id, api_key=api_key, timeout=zaman_asimi
                )
            else:
                sandbox = Sandbox(api_key=api_key, timeout=zaman_asimi)

            if not sandbox:
                raise Exception("Sandbox oluşturulamadı")

            # Kurulum komutlarını çalıştırma
            for cmd in kurulum_komutlari:
                sandbox.commands.run(cmd)

            # Kodu çalıştırma
            execution = sandbox.run_code(
                kod,
                language=dil.value,
                on_error=lambda e: sandbox.kill(),  # Hata olursa sandbox'u öldür
            )

            if execution.error:
                raise Exception(execution.error)

            yanit = execution.text
            stdout_loglari = "".join(execution.logs.stdout)
            stderr_loglari = "".join(execution.logs.stderr)

            return yanit, stdout_loglari, stderr_loglari

        except Exception as e:
            raise e

    def calistir(
        self, girdi_verisi: Girdi, *, kimlik_bilgileri: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        try:
            yanit, stdout_loglari, stderr_loglari = self.kod_yurut(
                girdi_verisi.kod,
                girdi_verisi.dil,
                girdi_verisi.kurulum_komutlari,
                girdi_verisi.zaman_asimi,
                kimlik_bilgileri.api_key.get_secret_value(),
                girdi_verisi.sablon_id,
            )

            if yanit:
                yield "yanit", yanit
            if stdout_loglari:
                yield "stdout_loglari", stdout_loglari
            if stderr_loglari:
                yield "stderr_loglari", stderr_loglari
        except Exception as e:
            yield "hata", str(e)
