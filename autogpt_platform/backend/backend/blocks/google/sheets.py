from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import SchemaField

from ._auth import (
    GOOGLE_OAUTH_IS_CONFIGURED,
    TEST_CREDENTIALS,
    TEST_CREDENTIALS_INPUT,
    GoogleCredentials,
    GoogleCredentialsField,
    GoogleCredentialsInput,
)


class GoogleSheetsReadBlock(Block):
    class Input(BlockSchema):
        credentials: GoogleCredentialsInput = GoogleCredentialsField(
            ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        )
        spreadsheet_id: str = SchemaField(
            description="Okunacak hesap tablosunun ID'si",
        )
        range: str = SchemaField(
            description="Okunacak aralığın A1 notasyonu",
        )

    class Output(BlockSchema):
        result: list[list[str]] = SchemaField(
            description="Hesap tablosundan okunan veriler",
        )
        error: str = SchemaField(
            description="Herhangi bir hata mesajı",
        )

    def __init__(self):
        super().__init__(
            id="5724e902-3635-47e9-a108-aaa0263a4988",
            description="Bu blok, bir Google Sheets hesap tablosundan veri okur.",
            categories={BlockCategory.DATA},
            input_schema=GoogleSheetsReadBlock.Input,
            output_schema=GoogleSheetsReadBlock.Output,
            disabled=not GOOGLE_OAUTH_IS_CONFIGURED,
            test_input={
                "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                "range": "Sheet1!A1:B2",
                "credentials": TEST_CREDENTIALS_INPUT,
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=[
                (
                    "result",
                    [
                        ["Name", "Score"],
                        ["Alice", "85"],
                    ],
                ),
            ],
            test_mock={
                "_read_sheet": lambda *args, **kwargs: [
                    ["Name", "Score"],
                    ["Alice", "85"],
                ],
            },
        )

    def run(
        self, input_data: Input, *, credentials: GoogleCredentials, **kwargs
    ) -> BlockOutput:
        service = self._build_service(credentials, **kwargs)
        data = self._read_sheet(service, input_data.spreadsheet_id, input_data.range)
        yield "result", data

    @staticmethod
    def _build_service(credentials: GoogleCredentials, **kwargs):
        creds = Credentials(
            token=(
                credentials.access_token.get_secret_value()
                if credentials.access_token
                else None
            ),
            refresh_token=(
                credentials.refresh_token.get_secret_value()
                if credentials.refresh_token
                else None
            ),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=kwargs.get("client_id"),
            client_secret=kwargs.get("client_secret"),
            scopes=credentials.scopes,
        )
        return build("sheets", "v4", credentials=creds)

    def _read_sheet(self, service, spreadsheet_id: str, range: str) -> list[list[str]]:
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range).execute()
        return result.get("values", [])


class GoogleSheetsWriteBlock(Block):
    class Input(BlockSchema):
        credentials: GoogleCredentialsInput = GoogleCredentialsField(
            ["https://www.googleapis.com/auth/spreadsheets"]
        )
        spreadsheet_id: str = SchemaField(
            description="Yazılacak hesap tablosunun ID'si",
        )
        range: str = SchemaField(
            description="Yazılacak aralığın A1 notasyonu",
        )
        values: list[list[str]] = SchemaField(
            description="Hesap tablosuna yazılacak veriler",
        )

    class Output(BlockSchema):
        result: dict = SchemaField(
            description="Yazma işleminin sonucu",
        )
        error: str = SchemaField(
            description="Herhangi bir hata mesajı",
        )

    def __init__(self):
        super().__init__(
            id="d9291e87-301d-47a8-91fe-907fb55460e5",
            description="Bu blok, bir Google Sheets hesap tablosuna veri yazar.",
            categories={BlockCategory.DATA},
            input_schema=GoogleSheetsWriteBlock.Input,
            output_schema=GoogleSheetsWriteBlock.Output,
            disabled=not GOOGLE_OAUTH_IS_CONFIGURED,
            test_input={
                "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
                "range": "Sheet1!A1:B2",
                "values": [
                    ["Name", "Score"],
                    ["Bob", "90"],
                ],
                "credentials": TEST_CREDENTIALS_INPUT,
            },
            test_credentials=TEST_CREDENTIALS,
            test_output=[
                (
                    "result",
                    {"updatedCells": 4, "updatedColumns": 2, "updatedRows": 2},
                ),
            ],
            test_mock={
                "_write_sheet": lambda *args, **kwargs: {
                    "updatedCells": 4,
                    "updatedColumns": 2,
                    "updatedRows": 2,
                },
            },
        )

    def run(
        self, input_data: Input, *, credentials: GoogleCredentials, **kwargs
    ) -> BlockOutput:
        service = GoogleSheetsReadBlock._build_service(credentials, **kwargs)
        result = self._write_sheet(
            service,
            input_data.spreadsheet_id,
            input_data.range,
            input_data.values,
        )
        yield "result", result

    def _write_sheet(
        self, service, spreadsheet_id: str, range: str, values: list[list[str]]
    ) -> dict:
        body = {"values": values}
        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        return result
