from abc import ABC, abstractmethod
from typing import Dict, Any
from app.schemas.inventory_analysis import InventoryAnalysisRequestWithSelection

class IInventoryAnalysisService(ABC):
    @abstractmethod
    async def get_enough_stock(self, request: InventoryAnalysisRequestWithSelection) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_excess_stock(self, request: InventoryAnalysisRequestWithSelection) -> Dict[str, Any]:
        pass
