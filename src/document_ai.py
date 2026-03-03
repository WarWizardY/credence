from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional

import pdfplumber
from PyPDF2 import PdfReader

try:
    import pytesseract  # type: ignore
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None  # type: ignore
    Image = None  # type: ignore


@dataclass
class FinancialFields:
    revenue: Optional[float] = None
    total_debt: Optional[float] = None
    contingent_liabilities: Optional[float] = None
    auditor_qualifications_present: bool = False


def _extract_text_pypdf(path: Path) -> str:
    reader = PdfReader(str(path))
    chunks: List[str] = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(chunks)


def _extract_text_ocr(path: Path) -> str:
    if pytesseract is None or Image is None:
        return ""
    try:
        import fitz  # type: ignore
    except Exception:
        # Fallback: no fitz, return empty
        return ""

    doc = fitz.open(str(path))
    texts: List[str] = []
    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        texts.append(pytesseract.image_to_string(img))
    return "\n".join(texts)


def extract_pdf_text_with_fallback(path: Path) -> str:
    """
    Try structured text extraction first; if we get almost nothing,
    fall back to OCR (for scanned PDFs).
    """
    text = _extract_text_pypdf(path)
    if len(text.strip()) < 100:
        ocr_text = _extract_text_ocr(path)
        if len(ocr_text.strip()) > len(text.strip()):
            return ocr_text
    return text


def extract_financial_fields_from_pdf(path: Path) -> FinancialFields:
    """
    Heuristic-based financial field extractor for large corporate annual reports.

    Key design:
    - First locate pages likely to contain financial statements (Balance Sheet,
      P&L, Cash Flow, Notes) using headings.
    - Then extract tables only from those pages (and immediate neighbours),
      instead of brute-forcing the entire document.
    """
    import re

    fields = FinancialFields()

    headings = [
        "consolidated balance sheet",
        "standalone balance sheet",
        "statement of profit and loss",
        "statement of profit & loss",
        "cash flow statement",
        "cashflow statement",
        "notes to the financial statements",
        "notes to accounts",
    ]

    candidate_pages: list[int] = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for idx, page in enumerate(pdf.pages):
                try:
                    text = (page.extract_text() or "").lower()
                except Exception:
                    continue
                if any(h in text for h in headings):
                    # add this page and immediate neighbours for table extraction
                    for j in range(max(0, idx - 1), min(len(pdf.pages), idx + 2)):
                        if j not in candidate_pages:
                            candidate_pages.append(j)

            # Fallback for short docs: if nothing detected, inspect first ~10 pages
            if not candidate_pages:
                candidate_pages = list(range(min(10, len(pdf.pages))))

            for page_index in candidate_pages:
                page = pdf.pages[page_index]
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row or len(row) < 2:
                            continue
                        label = " ".join(str(cell) for cell in row[:-1]).lower()
                        value_raw = row[-1]
                        if not value_raw:
                            continue
                        value_str = str(value_raw).replace(",", "").replace("₹", "").strip()
                        try:
                            value = float(re.sub(r"[^\d.\-]", "", value_str))
                        except ValueError:
                            continue
                        if "revenue" in label or "total income" in label:
                            fields.revenue = fields.revenue or value
                        elif "borrowings" in label or "total debt" in label:
                            fields.total_debt = fields.total_debt or value
                        elif "contingent liabilities" in label:
                            fields.contingent_liabilities = fields.contingent_liabilities or value
    except Exception:
        pass

    # 2) Scan text for auditor remarks / qualifications – only to set a flag
    text = extract_pdf_text_with_fallback(path).lower()
    if any(kw in text for kw in ["qualified opinion", "emphasis of matter", "going concern", "adverse opinion"]):
        fields.auditor_qualifications_present = True

    return fields


def segment_pdf_sections(path: Path) -> Dict[str, Any]:
    """
    Rough section segmentation for very long reports: try to locate
    indices for management discussion, financials, notes, etc.
    """
    section_markers = {
        "md&a": ["management discussion and analysis", "management discussion & analysis"],
        "financial_statements": ["standalone financial statements", "consolidated financial statements"],
        "notes_to_accounts": ["notes to the financial statements", "notes forming part of"],
        "auditors_report": ["independent auditors report", "auditor’s report"],
    }

    sections: Dict[str, Any] = {}
    try:
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages):
                text = (page.extract_text() or "").lower()
                for key, markers in section_markers.items():
                    if key in sections:
                        continue
                    if any(m in text for m in markers):
                        sections[key] = {"start_page": i + 1}
    except Exception:
        pass

    return sections

