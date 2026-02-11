from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AthenaPaginatedResult(BaseModel):
    """
    Athena specific pagination result schema.
    """
    results: List[Dict[str, Any]]
    executionId: str
    nextToken: Optional[str] = None
    hasMore: bool
