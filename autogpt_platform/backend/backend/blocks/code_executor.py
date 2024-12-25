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
class ProgrammingLanguage(Enum):
    PYTHON = "python"
    JAVASCRIPT = "js"
    BASH = "bash"
    R = "r"
    JAVA = "java"

# Kod yürütme bloğu
class CodeExecutionBlock(Block):
    # TODO : Dosya yükleme ve indirme desteği ekle
    # Şu anda, CPU ve Belleği yalnızca önceden özelleştirilmiş bir sandbox şablonu oluşturarak özelleştirebilirsiniz
    class Input(BlockSchema):
        credentials: CredentialsMetaInput[
            Literal[ProviderName.E2B], Literal["api_key"]
        ] = CredentialsField(
            description="E2B Sandbox için API anahtarınızı girin. Buradan alabilirsiniz - https://e2b.dev/docs",
        )

        # TODO : Komutları arka planda çalıştırma seçeneği ekle
        setup_commands: list[str] = SchemaField(
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

        code: str = SchemaField(
            description="Sandbox içinde çalıştırılacak kod",
            placeholder="print('Merhaba, Dünya!')",
            default="",
            advanced=False,
        )

        language: ProgrammingLanguage = SchemaField(
            description="Çalıştırılacak programlama dili",
            default=ProgrammingLanguage.PYTHON,
            advanced=False,
        )

        timeout: int = SchemaField(
            description="Çalıştırma zaman aşımı süresi (saniye cinsinden)", default=300
        )

        template_id: str = SchemaField(
            description=(
                "Bir E2B sandbox şablonu kullanabilirsiniz, bunun için buraya ID'sini girin. "
                "Daha fazla detay için E2B dokümanlarına bakın: "
                "[E2B - Sandbox template](https://e2b.dev/docs/sandbox-template)"
            ),
            default="",
            advanced=True,
        )

    class Output(BlockSchema):
        response: str = SchemaField(description="Kod yürütme yanıtı")
        stdout_logs: str = SchemaField(
            description="Çalıştırma sırasında standart çıktı logları"
        )
        stderr_logs: str = SchemaField(description="Çalıştırma sırasında standart hata logları")
        error: str = SchemaField(description="Çalıştırma başarısız olursa hata mesajı")

    def __init__(self):
        super().__init__(
            id="0b02b072-abe7-11ef-8372-fb5d162dd712",
            description="İnternet erişimi olan izole bir sandbox ortamında kod çalıştırır.",
            categories={BlockCategory.DEVELOPER_TOOLS},
            input_schema=CodeExecutionBlock.Input,
            output_schema=CodeExecutionBlock.Output,
            test_credentials=TEST_CREDENTIALS,
            test_input={
                "credentials": TEST_CREDENTIALS_INPUT,
                "code": "print('Merhaba Dünya')",
                "language": ProgrammingLanguage.PYTHON.value,
                "setup_commands": [],
                "timeout": 300,
                "template_id": "",
            },
            test_output=[
                ("response", "Merhaba Dünya"),
                ("stdout_logs", "Merhaba Dünya\n"),
            ],
            test_mock={
                "execute_code": lambda code, language, setup_commands, timeout, api_key, template_id: (
                    "Merhaba Dünya",
                    "Merhaba Dünya\n",
                    "",
                ),
            },
        )

    def execute_code(
        self,
        code: str,
        language: ProgrammingLanguage,
        setup_commands: list[str],
        timeout: int,
        api_key: str,
        template_id: str,
    ):
        try:
            sandbox = None
            if template_id:
                sandbox = Sandbox(
                    template=template_id, api_key=api_key, timeout=timeout
                )
            else:
                sandbox = Sandbox(api_key=api_key, timeout=timeout)

            if not sandbox:
                raise Exception("Sandbox oluşturulamadı")

            # Kurulum komutlarını çalıştırma
            for cmd in setup_commands:
                sandbox.commands.run(cmd)

            # Kodu çalıştırma
            execution = sandbox.run_code(
                code,
                language=language.value,
                on_error=lambda e: sandbox.kill(),  # Hata olursa sandbox'u öldür
            )

            if execution.error:
                raise Exception(execution.error)

            response = execution.text
            stdout_logs = "".join(execution.logs.stdout)
            stderr_logs = "".join(execution.logs.stderr)

            return response, stdout_logs, stderr_logs

        except Exception as e:
            raise e

    def run(
        self, input_data: Input, *, credentials: APIKeyCredentials, **kwargs
    ) -> BlockOutput:
        try:
            response, stdout_logs, stderr_logs = self.execute_code(
                input_data.code,
                input_data.language,
                input_data.setup_commands,
                input_data.timeout,
                credentials.api_key.get_secret_value(),
                input_data.template_id,
            )

            if response:
                yield "response", response
            if stdout_logs:
                yield "stdout_logs", stdout_logs
            if stderr_logs:
                yield "stderr_logs", stderr_logs
        except Exception as e:
            yield "error", str(e)
