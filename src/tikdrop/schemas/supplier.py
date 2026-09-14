from pydantic import BaseModel


class SupplierInput(BaseModel):
    """Maps 1:1 to the supplier checklist in idea.pdf Anexo A."""

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
