from typing import Optional

from pydantic import BaseModel


class VatCheckResult(BaseModel):
    """Result of an EU VIES VAT number check (idea.pdf Anexo A / section 9)."""

    country_code: str
    vat_number: str
    valid: bool
    name: Optional[str] = None
    address: Optional[str] = None
    request_date: Optional[str] = None
