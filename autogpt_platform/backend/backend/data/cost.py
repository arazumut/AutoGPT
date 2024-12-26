from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel

from backend.data.block import BlockInput


class BlockCostType(str, Enum):
    RUN = "run"  # çalıştırma başına X kredi maliyeti
    BYTE = "byte"  # byte başına X kredi maliyeti
    SECOND = "second"  # saniye başına X kredi maliyeti
    DOLLAR = "dollar"  # çalıştırma başına X dolar maliyeti


class BlockCost(BaseModel):
    maliyet_miktari: int
    maliyet_filtre: BlockInput
    maliyet_tipi: BlockCostType

    def __init__(
        self,
        maliyet_miktari: int,
        maliyet_tipi: BlockCostType = BlockCostType.RUN,
        maliyet_filtre: Optional[BlockInput] = None,
        **veri: Any,
    ) -> None:
        super().__init__(
            cost_amount=maliyet_miktari,
            cost_filter=maliyet_filtre or {},
            cost_type=maliyet_tipi,
            **veri,
        )
