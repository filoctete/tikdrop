"""EU VIES VAT number validation: official European Commission service, free, no API key.
Automates one item of the supplier checklist (idea.pdf Anexo A / development_guide.pdf
section 9): "Validar VAT quando aplicável através do VIES".
"""

from typing import Optional

import httpx

from tikdrop.schemas.vat import VatCheckResult

_VIES_URL = "https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number"


class ViesError(RuntimeError):
    """Raised when the VIES service is unreachable or returns something we can't use."""


def check_vat(country_code: str, vat_number: str) -> VatCheckResult:
    clean_country = country_code.strip().upper()
    clean_number = vat_number.replace(" ", "").replace(country_code, "", 1) if vat_number.upper().startswith(clean_country) else vat_number.replace(" ", "")

    response = httpx.post(
        _VIES_URL,
        json={"countryCode": clean_country, "vatNumber": clean_number},
        timeout=15.0,
    )
    if response.status_code != 200:
        raise ViesError(f"VIES check failed {response.status_code}: {response.text}")

    data = response.json()
    return VatCheckResult(
        country_code=data.get("countryCode", clean_country),
        vat_number=data.get("vatNumber", clean_number),
        valid=bool(data.get("valid")),
        # Some member states (Portugal included) return "---" instead of actual name/address
        # for privacy reasons - treat that the same as "not provided".
        name=_clean_field(data.get("name")),
        address=_clean_field(data.get("address")),
        request_date=data.get("requestDate"),
    )


def _clean_field(value: object) -> Optional[str]:
    text = (value or "").strip()
    return text if text and text.strip("-") else None
