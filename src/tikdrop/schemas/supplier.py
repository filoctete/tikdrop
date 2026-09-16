from typing import Optional

from pydantic import BaseModel


class SupplierInput(BaseModel):
    """Maps 1:1 to the supplier checklist in idea.pdf Anexo A."""

    listing_url: Optional[str] = None  # the exact product listing chosen - not a scoring input,
    # just kept so the specific supplier/listing behind the numbers isn't lost
    identity_verified: bool = False
    vat_validated: bool = False
    eu_warehouse: bool = False
    dropshipping_confirmed: bool = False
    neutral_packaging_possible: bool = False
    tracking_available: bool = False
    returns_policy_clear: bool = False
    integration_available: bool = False
    test_order_completed: bool = False
    backup_supplier_identified: bool = False
