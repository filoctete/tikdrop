"""Standalone EU VAT check via VIES (free, official, no API key) - part of the supplier
checklist (idea.pdf Anexo A). Run with:
  python examples/check_supplier_vat.py PT 509442083
"""

import sys

from tikdrop.ingestion import ViesError, check_vat


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python examples/check_supplier_vat.py <country_code> <vat_number>")
        print("Example: python examples/check_supplier_vat.py PT 509442083")
        return

    country_code, vat_number = sys.argv[1], sys.argv[2]

    try:
        result = check_vat(country_code, vat_number)
    except ViesError as exc:
        print(f"VIES check failed: {exc}")
        return

    print(f"{result.country_code}{result.vat_number}: {'VALID' if result.valid else 'NOT VALID'}")
    if result.name:
        print(f"  Name: {result.name}")
    if result.address:
        print(f"  Address: {result.address}")


if __name__ == "__main__":
    main()
