from tikdrop.profit.engine import ProfitEngine
from tikdrop.schemas.profit import CostInputs


def test_viable_product_has_positive_net_contribution():
    costs = CostInputs(
        sale_price=25.0,
        product_cost=5.0,
        shipping_cost=3.0,
        payment_fees=1.0,
        ad_cost_per_unit=6.0,
        returns_cost_estimate=1.0,
        other_costs=1.0,
    )

    result = ProfitEngine.calculate(costs)

    assert result.gross_margin == 20.0
    assert result.contribution_margin == 25.0 - 5.0 - 3.0 - 1.0 - 6.0 - 1.0
    assert result.net_contribution == result.contribution_margin - 1.0
    assert result.is_viable is True
    assert result.net_contribution_pct == result.net_contribution / 25.0


def test_unviable_product_when_costs_exceed_price():
    costs = CostInputs(
        sale_price=10.0,
        product_cost=4.0,
        shipping_cost=3.0,
        payment_fees=1.0,
        ad_cost_per_unit=4.0,
        returns_cost_estimate=1.0,
    )

    result = ProfitEngine.calculate(costs)

    assert result.net_contribution < 0
    assert result.is_viable is False
