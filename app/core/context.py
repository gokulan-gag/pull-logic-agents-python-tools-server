from contextvars import ContextVar
from typing import Optional

# Context variable to store the company ID for the duration of a request
company_id_ctx: ContextVar[Optional[str]] = ContextVar("company_id", default=None)

def get_company_id() -> Optional[str]:
    """Retrieve the current company ID from the context."""
    return company_id_ctx.get()

def set_company_id(company_id: str) -> None:
    """Set the company ID in the context."""
    company_id_ctx.set(company_id)
