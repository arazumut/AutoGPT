import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pydantic import BaseModel, ConfigDict

from backend.data.block import Block, BlockCategory, BlockOutput, BlockSchema
from backend.data.model import BlockSecret, SchemaField, SecretField


class EmailKimlikBilgileri(BaseModel):
    smtp_sunucusu: str = SchemaField(
        default="smtp.gmail.com", description="SMTP sunucu adresi"
    )
    smtp_portu: int = SchemaField(default=25, description="SMTP port numarası")
    smtp_kullanici_adi: BlockSecret = SecretField(key="smtp_kullanici_adi")
    smtp_sifre: BlockSecret = SecretField(key="smtp_sifre")

    model_config = ConfigDict(title="Email Kimlik Bilgileri")


class EmailGondermeBloğu(Block):
    class Girdi(BlockSchema):
        alici_email: str = SchemaField(
            description="Alıcının email adresi", placeholder="alici@example.com"
        )
        konu: str = SchemaField(
            description="Email konusu", placeholder="Email konusunu girin"
        )
        govde: str = SchemaField(
            description="Email gövdesi", placeholder="Email gövdesini girin"
        )
        kimlik_bilgileri: EmailKimlikBilgileri = SchemaField(
            description="SMTP kimlik bilgileri",
            default=EmailKimlikBilgileri(),
        )

    class Cikti(BlockSchema):
        durum: str = SchemaField(description="Email gönderme işleminin durumu")
        hata: str = SchemaField(
            description="Email gönderme başarısız olursa hata mesajı"
        )

    def __init__(self):
        super().__init__(
            disabled=True,
            id="4335878a-394e-4e67-adf2-919877ff49ae",
            description="Bu blok sağlanan SMTP kimlik bilgilerini kullanarak email gönderir.",
            categories={BlockCategory.OUTPUT},
            input_schema=EmailGondermeBloğu.Girdi,
            output_schema=EmailGondermeBloğu.Cikti,
            test_input={
                "alici_email": "alici@example.com",
                "konu": "Test Email",
                "govde": "Bu bir test emailidir.",
                "kimlik_bilgileri": {
                    "smtp_sunucusu": "smtp.gmail.com",
                    "smtp_portu": 25,
                    "smtp_kullanici_adi": "your-email@gmail.com",
                    "smtp_sifre": "your-gmail-password",
                },
            },
            test_output=[("durum", "Email başarıyla gönderildi")],
            test_mock={"email_gonder": lambda *args, **kwargs: "Email başarıyla gönderildi"},
        )

    @staticmethod
    def email_gonder(
        kimlik_bilgileri: EmailKimlikBilgileri, alici_email: str, konu: str, govde: str
    ) -> str:
        smtp_sunucusu = kimlik_bilgileri.smtp_sunucusu
        smtp_portu = kimlik_bilgileri.smtp_portu
        smtp_kullanici_adi = kimlik_bilgileri.smtp_kullanici_adi.get_secret_value()
        smtp_sifre = kimlik_bilgileri.smtp_sifre.get_secret_value()

        msg = MIMEMultipart()
        msg["From"] = smtp_kullanici_adi
        msg["To"] = alici_email
        msg["Subject"] = konu
        msg.attach(MIMEText(govde, "plain"))

        with smtplib.SMTP(smtp_sunucusu, smtp_portu) as server:
            server.starttls()
            server.login(smtp_kullanici_adi, smtp_sifre)
            server.sendmail(smtp_kullanici_adi, alici_email, msg.as_string())

        return "Email başarıyla gönderildi"

    def run(self, girdi_verisi: Girdi, **kwargs) -> BlockOutput:
        yield "durum", self.email_gonder(
            girdi_verisi.kimlik_bilgileri,
            girdi_verisi.alici_email,
            girdi_verisi.konu,
            girdi_verisi.govde,
        )
