from tikdrop.schemas.profit import CostInputs, MarginResult


class ProfitEngine:
    """Deterministic unit economics, per development_guide.pdf section 9:

    sale_price - product - shipping - fees - ads - returns - other_costs = contribution margin
    """

    @staticmethod
    def calculate(costs: CostInputs) -> MarginResult:
        gross_margin = costs.sale_price - costs.product_cost

        contribution_margin = (
            costs.sale_price
            - costs.product_cost
            - costs.shipping_cost
            - costs.payment_fees
            - costs.ad_cost_per_unit
            - costs.returns_cost_estimate
        )

        net_contribution = contribution_margin - costs.other_costs

        return MarginResult(
            gross_margin=gross_margin,
            contribution_margin=contribution_margin,
            contribution_margin_pct=contribution_margin / costs.sale_price,
            net_contribution=net_contribution,
            net_contribution_pct=net_contribution / costs.sale_price,
            is_viable=net_contribution > 0,
        )
