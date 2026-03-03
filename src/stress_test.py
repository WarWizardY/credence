from __future__ import annotations

from typing import List, Dict, Any

from .risk_engine import RiskInputs, simple_rule_based_decision


def run_stress_tests(
    base_features: RiskInputs,
    requested_limit: float,
    sector: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Simple sensitivity analysis around the rule-based engine.
    Scenarios are illustrative only.
    """
    scenarios = []

    def clone_features(**overrides: Any) -> RiskInputs:
        data = base_features.__dict__.copy()
        data.update(overrides)
        return RiskInputs(**data)

    # Scenario 1: Revenue -20%
    f1 = clone_features(latest_revenue=base_features.latest_revenue * 0.8)
    d1 = simple_rule_based_decision(f1, requested_limit=requested_limit, sector=sector)
    scenarios.append(
        {
            "name": "Revenue -20%",
            "score": d1.score,
            "risk_band": d1.risk_band,
            "recommended_limit": d1.recommended_limit,
            "recommended_rate": d1.recommended_rate,
        }
    )

    # Scenario 2: EBITDA margin compressed (EBITDA -30%)
    f2 = clone_features(latest_ebitda=base_features.latest_ebitda * 0.7)
    d2 = simple_rule_based_decision(f2, requested_limit=requested_limit, sector=sector)
    scenarios.append(
        {
            "name": "EBITDA -30%",
            "score": d2.score,
            "risk_band": d2.risk_band,
            "recommended_limit": d2.recommended_limit,
            "recommended_rate": d2.recommended_rate,
        }
    )

    # Scenario 3: Elevated anomaly scores
    f3 = clone_features()
    # In a fuller implementation we would explicitly include anomaly scores in RiskInputs;
    # here we simply re-use the same features and note that this is a placeholder.
    d3 = simple_rule_based_decision(f3, requested_limit=requested_limit, sector=sector)
    scenarios.append(
        {
            "name": "Anomaly stress (placeholder)",
            "score": d3.score,
            "risk_band": d3.risk_band,
            "recommended_limit": d3.recommended_limit,
            "recommended_rate": d3.recommended_rate,
        }
    )

    return scenarios

