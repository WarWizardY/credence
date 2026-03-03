from pathlib import Path
from typing import Dict, Any

from PyPDF2 import PdfReader
import pandas as pd


def _extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    texts: list[str] = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(texts)


def analyze_cibil_pdf(path: Path) -> Dict[str, Any]:
    """
    Very lightweight parser for CIBIL commercial report PDFs.
    Uses keyword matches as proxies for risk.
    """
    text = _extract_pdf_text(path).lower()

    high_risk_terms = ["write-off", "settled", "wilful defaulter", "loss", "doubtful"]
    dpd_terms = ["30+ dpd", "60+ dpd", "90+ dpd", "dpd"]

    high_risk_hits = sum(text.count(t) for t in high_risk_terms)
    dpd_hits = sum(text.count(t) for t in dpd_terms)

    cibil_risk_score = max(0.0, min(1.0, (high_risk_hits + dpd_hits) / 10.0)) if (high_risk_hits + dpd_hits) > 0 else 0.0

    return {
        "cibil_risk_score": float(cibil_risk_score),
        "cibil_high_risk_hits": high_risk_hits,
        "cibil_dpd_hits": dpd_hits,
    }


def analyze_epfo_payroll(csv_path: Path) -> Dict[str, Any]:
    """
    Prototype analysis of EPFO / payroll statement (assumed CSV).
    Expects columns like: month, employee_id, wage.
    """
    df = pd.read_csv(csv_path)
    if df.empty:
        return {"payroll_stability_score": 0.5, "employee_count": 0}

    employee_count = df["employee_id"].nunique() if "employee_id" in df.columns else None
    months = df["month"].nunique() if "month" in df.columns else None

    payroll_stability_score = 0.5
    if months and months >= 6:
        payroll_stability_score = 0.7
    if months and months >= 12:
        payroll_stability_score = 0.9

    return {
        "payroll_stability_score": float(payroll_stability_score),
        "employee_count": int(employee_count or 0),
        "payroll_months": int(months or 0),
    }


def analyze_related_party_ledger(csv_path: Path) -> Dict[str, Any]:
    """
    Prototype analysis of related party ledger (assumed CSV).
    Expects columns like: counterparty_name, amount, type (loan/sale/purchase).
    We approximate risk via concentration and volume of related party transactions.
    """
    df = pd.read_csv(csv_path)
    if df.empty:
        return {"related_party_risk_score": 0.0}

    total = df["amount"].abs().sum() if "amount" in df.columns else 0.0
    top_counterparty_share = 0.0
    if "counterparty_name" in df.columns and "amount" in df.columns and total > 0:
        grouped = df.groupby("counterparty_name")["amount"].sum().abs()
        top_counterparty_share = float(grouped.max() / total)

    # Higher share of single related party implies higher risk
    related_party_risk_score = max(0.0, min(1.0, top_counterparty_share * 2.0))

    return {
        "related_party_risk_score": float(related_party_risk_score),
        "related_party_total_volume": float(total),
        "related_party_top_share": float(top_counterparty_share),
    }

