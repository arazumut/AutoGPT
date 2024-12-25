import logging

from colorama import Fore, Style
from google.cloud.logging_v2.handlers import CloudLoggingFilter, StructuredLogHandler

from .utils import remove_color_codes


class FancyConsoleFormatter(logging.Formatter):
    """
    Konsol çıktısı için özel bir log formatlayıcı.

    Bu formatlayıcı, standart log çıktısını renk kodlaması ile zenginleştirir. Renk
    kodlaması, log mesajının seviyesine göre belirlenir ve konsol çıktısında farklı
    türdeki mesajları ayırt etmeyi kolaylaştırır.

    Her seviye için renk, LEVEL_COLOR_MAP sınıf özniteliğinde tanımlanmıştır.
    """

    # seviye -> (seviye & metin rengi, başlık rengi)
    LEVEL_COLOR_MAP = {
        logging.DEBUG: Fore.LIGHTBLACK_EX,
        logging.INFO: Fore.BLUE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        # `msg`'in bir string olduğundan emin olun
        if not hasattr(record, "msg"):
            record.msg = ""
        elif type(record.msg) is not str:
            record.msg = str(record.msg)

        # Hata seviyesine göre varsayılan rengi belirleyin
        level_color = ""
        if record.levelno in self.LEVEL_COLOR_MAP:
            level_color = self.LEVEL_COLOR_MAP[record.levelno]
            record.levelname = f"{level_color}{record.levelname}{Style.RESET_ALL}"

        # Mesaj için rengi belirleyin
        color = getattr(record, "color", level_color)
        color_is_specified = hasattr(record, "color")

        # Renk belirtilmedikçe INFO mesajlarını renklendirmeyin.
        if color and (record.levelno != logging.INFO or color_is_specified):
            record.msg = f"{color}{record.msg}{Style.RESET_ALL}"

        return super().format(record)


class AGPTFormatter(FancyConsoleFormatter):
    def __init__(self, *args, no_color: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.no_color = no_color

    def format(self, record: logging.LogRecord) -> str:
        # `msg`'in bir string olduğundan emin olun
        if not hasattr(record, "msg"):
            record.msg = ""
        elif type(record.msg) is not str:
            record.msg = str(record.msg)

        # Renk kodlarını kaldırarak mesajı renk sahtekarlığından koruyun
        if record.msg and not getattr(record, "preserve_color", False):
            record.msg = remove_color_codes(record.msg)

        # Başlık için rengi belirleyin
        title = getattr(record, "title", "")
        title_color = getattr(record, "title_color", "") or self.LEVEL_COLOR_MAP.get(
            record.levelno, ""
        )
        if title and title_color:
            title = f"{title_color + Style.BRIGHT}{title}{Style.RESET_ALL}"
        # record.title'ın ayarlandığından ve boş değilse bir boşluk ile doldurulduğundan emin olun
        record.title = f"{title} " if title else ""

        if self.no_color:
            return remove_color_codes(super().format(record))
        else:
            return super().format(record)


class StructuredLoggingFormatter(StructuredLogHandler, logging.Formatter):
    def __init__(self):
        # Log kayıtlarına tanısal bilgi eklemek için CloudLoggingFilter'ı ayarlayın
        self.cloud_logging_filter = CloudLoggingFilter()

        # StructuredLogHandler'ı başlatın
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        self.cloud_logging_filter.filter(record)
        return super().format(record)
