from tikdrop.profit.engine import ProfitEngine
from tikdrop.schemas.score import DimensionScore, ProductScoreInput, ProductScoreResult
from tikdrop.scoring import dimensions as dim

# Anexo B (idea.pdf) / section 7 (development_guide.pdf) - must sum to 1.0
WEIGHTS = {
    "trend": 0.20,
    "portugal_opportunity": 0.20,
    "margin": 0.20,
    "supplier": 0.15,
    "creative": 0.10,
    "logistics": 0.10,
    "risk_compliance": 0.05,
}

# idea.pdf section 17: "Produto já saturado em Portugal - Obrigar o scoring a penalizar
# concorrência e não lançar sem diferenciação." Encoded as an explicit override so a high
# total score can't paper over an undifferentiated, saturated PT market.
_SATURATION_OVERRIDE_OPPORTUNITY_THRESHOLD = 4.0
_SATURATION_OVERRIDE_DIFFERENTIATION_THRESHOLD = 5.0


class ProductScoringEngine:
    @staticmethod
    def score(inp: ProductScoreInput) -> ProductScoreResult:
        margin_result = ProfitEngine.calculate(inp.costs)

        raw_scores = {
            "trend": dim.score_trend(inp.trend),
            "portugal_opportunity": dim.score_portugal_opportunity(inp.portugal_opportunity),
            "margin": dim.score_margin(margin_result.net_contribution_pct),
            "supplier": dim.score_supplier(inp.supplier),
            "creative": dim.score_creative(inp.creative),
            "logistics": dim.score_logistics(inp.logistics),
            "risk_compliance": dim.score_risk_compliance(inp.risk_compliance),
        }

        dimensions = {
            name: DimensionScore(
                raw_score=raw,
                weight=WEIGHTS[name],
                weighted_contribution=raw * WEIGHTS[name],
            )
            for name, raw in raw_scores.items()
        }

        total_score = sum(d.weighted_contribution for d in dimensions.values())

        saturated_undifferentiated = (
            raw_scores["portugal_opportunity"] < _SATURATION_OVERRIDE_OPPORTUNITY_THRESHOLD
            and inp.portugal_opportunity.differentiation_score < _SATURATION_OVERRIDE_DIFFERENTIATION_THRESHOLD
        )

        if not margin_result.is_viable:
            recommendation = "reject"
            reason = "Net contribution margin is not positive."
        elif saturated_undifferentiated:
            recommendation = "reject"
            reason = "PT market looks saturated and no strong differentiation angle was given."
        elif total_score >= 7.0:
            recommendation = "test"
            reason = "Total score clears the test threshold (>=7)."
        elif total_score >= 5.0:
            recommendation = "watch"
            reason = "Borderline score (5-7): re-evaluate once more signals/data come in."
        else:
            recommendation = "reject"
            reason = "Total score is below the minimum bar (<5)."

        return ProductScoreResult(
            product_name=inp.product_name,
            dimensions=dimensions,
            total_score=total_score,
            recommendation=recommendation,
            recommendation_reason=reason,
        )
