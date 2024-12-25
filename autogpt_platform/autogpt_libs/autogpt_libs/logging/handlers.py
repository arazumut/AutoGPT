from __future__ import annotations

import json
import logging


class JsonDosyaHandler(logging.FileHandler):
    def format(self, record: logging.LogRecord) -> str:
        # Log kaydının mesajını JSON formatında ayrıştır
        record.json_data = json.loads(record.getMessage())
        # JSON verisini güzel bir şekilde formatla ve döndür
        return json.dumps(getattr(record, "json_data"), ensure_ascii=False, indent=4)

    def emit(self, record: logging.LogRecord) -> None:
        # Log kaydını dosyaya yaz
        with open(self.baseFilename, "w", encoding="utf-8") as f:
            f.write(self.format(record))
