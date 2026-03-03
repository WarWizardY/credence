from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional

import re

from .document_ai import extract_pdf_text_with_fallback


@dataclass
class SanctionLoanDetails:
    loan_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    tenure_months: Optional[int] = None
    facility_type: Optional[str] = None
    guarantee_type: Optional[str] = None
    bank_name: Optional[str] = None


def _parse_loan_amount(text: str) -> Optional[float]:
    """
    Very lightweight parser for sanctioned / loan amount.
    Looks for patterns like:
        "Loan Amount: 30,000"
        "Sanctioned amount of INR 30,000"
    """
    patterns = [
        r"(loan amount|sanction(?:ed)? amount|amount sanctioned)[^\d]{0,40}([\d,]+(?:\.\d+)?)",
        r"amount of\s+rs\.?\s*([\d,]+(?:\.\d+)?)",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            raw = m.group(2 if m.lastindex and m.lastindex >= 2 else 1)
            raw = raw.replace(",", "")
            try:
                return float(raw)
            except ValueError:
                continue
    return None


def _parse_interest_rate(text: str) -> Optional[float]:
    """
    Parse interest rate in patterns like:
        "Interest rate: 23.25% p.a."
        "ROI 23.25 %"
    """
    patterns = [
        r"(interest rate|roi)[^\d]{0,40}(\d{1,2}(?:\.\d+)?)\s*%",
        r"(\d{1,2}(?:\.\d+)?)\s*%\s*(?:p\.?a\.?|per annum)",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            raw = m.group(2 if m.lastindex and m.lastindex >= 2 else 1)
            try:
                return float(raw)
            except ValueError:
                continue
    return None


def _parse_tenure_months(text: str) -> Optional[int]:
    """
    Parse loan tenure like:
        "Tenure: 6 months"
        "Loan period of 24 months"
        "Tenor 3 years"
    """
    patterns = [
        r"(tenure|tenor|loan period)[^\d]{0,40}(\d{1,3})\s*(months?|mths?)",
        r"(tenure|tenor|loan period)[^\d]{0,40}(\d{1,2})\s*(years?|yrs?)",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            num_str = m.group(2)
            unit = m.group(3).lower()
            try:
                num = int(num_str)
            except ValueError:
                continue
            if "year" in unit or "yr" in unit:
                return num * 12
            return num
    return None


def _detect_facility_type(text: str) -> Optional[str]:
    """
    Heuristic detection of facility type from common Indian banking terms.
    """
    lowered = text.lower()
    if "term loan" in lowered:
        return "Term Loan"
    if "cash credit" in lowered or "cc facility" in lowered:
        return "Cash Credit"
    if "overdraft" in lowered or "od facility" in lowered:
        return "Overdraft"
    if "working capital" in lowered:
        return "Working Capital"
    return None


def _detect_guarantee_type(text: str) -> Optional[str]:
    """
    Detect common guarantee / scheme markers.
    """
    lowered = text.lower()
    if "jlg" in lowered or "joint liability group" in lowered:
        return "JLG"
    if "cgtmse" in lowered:
        return "CGTMSE"
    if "collateral free" in lowered:
        return "Collateral Free"
    return None


def _detect_bank_name(original_text: str) -> Optional[str]:
    """
    Very rough bank name detector – looks for 'Something Bank' in the first
    few hundred characters.
    """
    head = original_text[:600]
    m = re.search(r"([A-Z][A-Za-z& ]+ Bank)", head)
    if m:
        return m.group(1).strip()
    return None


def extract_sanction_loan_features(path: Path) -> Dict[str, Any]:
    """
    Extract a small set of structured features from a sanction letter PDF.

    This is intentionally heuristic and designed to be resilient:
    - If nothing is detected, returns an empty dict.
    - If partial information is detected, returns only those keys.
    """
    raw_text = extract_pdf_text_with_fallback(path)
    if not raw_text.strip():
        return {}

    lowered = raw_text.lower()

    loan_amount = _parse_loan_amount(raw_text)
    interest_rate = _parse_interest_rate(raw_text)
    tenure_months = _parse_tenure_months(raw_text)
    facility_type = _detect_facility_type(lowered)
    guarantee_type = _detect_guarantee_type(lowered)
    bank_name = _detect_bank_name(raw_text)

    # If we don't at least get a loan_amount, treat it as "not a sanction letter"
    if loan_amount is None:
        return {}

    features: Dict[str, Any] = {
        "sanction_loan_amount": float(loan_amount),
    }
    if interest_rate is not None:
        features["sanction_interest_rate"] = float(interest_rate)
    if tenure_months is not None:
        features["sanction_tenure_months"] = int(tenure_months)
    if facility_type:
        features["sanction_facility_type"] = facility_type
    if guarantee_type:
        features["sanction_guarantee_type"] = guarantee_type
    if bank_name:
        features["sanction_bank_name"] = bank_name

    # Derived behavioral flags for the risk engine
    features["sanction_existing_debt"] = float(loan_amount)
    if interest_rate is not None:
        features["sanction_effective_rate"] = float(interest_rate)
        features["sanction_high_interest_flag"] = interest_rate > 20.0
    if tenure_months is not None:
        features["sanction_short_tenure_flag"] = tenure_months <= 12

    microfinance_flag = False
    group_liability_flag = False
    if guarantee_type and guarantee_type.upper() == "JLG":
        microfinance_flag = True
        group_liability_flag = True

    features["sanction_microfinance_exposure_flag"] = microfinance_flag
    features["sanction_group_liability_flag"] = group_liability_flag

    return features

