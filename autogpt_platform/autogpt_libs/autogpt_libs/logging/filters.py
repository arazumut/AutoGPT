import logging

class AltSeviyeFiltresi(logging.Filter):
    """Belirli bir eşik seviyesinin altındaki günlük kayıtlarını filtreler."""

    def __init__(self, alt_seviye: int):
        super().__init__()
        self.alt_seviye = alt_seviye

    def filter(self, kayit: logging.LogRecord):
        return kayit.levelno < self.alt_seviye
