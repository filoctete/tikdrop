from tikdrop.compliance import suggest_risk_compliance


def test_unmatched_product_is_low_risk():
    result = suggest_risk_compliance("silicone pet hair roller")

    assert result.category_risk_level == "low"
    assert result.is_regulated_category is False


def test_matches_supplement_keyword_case_insensitively():
    result = suggest_risk_compliance("Whey Protein Powder 1kg")

    assert result.category_risk_level == "high"
    assert result.is_regulated_category is True


def test_matches_portuguese_keyword():
    result = suggest_risk_compliance("Creme facial anti-idade")

    assert result.category_risk_level == "high"


def test_medical_device_also_flags_technical_documentation():
    result = suggest_risk_compliance("Joelheira ortopédica")

    assert result.category_risk_level == "high"
    assert result.requires_technical_documentation is True


def test_toy_does_not_require_technical_documentation():
    result = suggest_risk_compliance("Brinquedo educativo")

    assert result.category_risk_level == "high"
    assert result.requires_technical_documentation is False
