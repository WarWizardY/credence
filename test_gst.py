import os
import json
from dotenv import load_dotenv
from src.document_parser.parser import DocumentParser

load_dotenv()

text = """
GLOBALFORGE INDUSTRIES PVT. LTD.

Comprehensive Indirect Tax Compliance Statement
Financial Year: 2024–25
GSTIN: 27AAHCG4589Q1ZK
State: Maharashtra

1. Aggregate Turnover & Output Tax Position

During the financial year under review, the Company recorded gross taxable outward supplies amounting to INR 21,95,00,000, comprising domestic and export transactions.

Domestic taxable supplies aggregated to INR 18,75,00,000, attracting tax components as under:

Central Tax: INR 1,68,75,000

State Tax: INR 1,68,75,000

Integrated Tax: INR 92,40,000

Export supplies (zero-rated) amounted to INR 3,20,00,000, on which Integrated Tax of INR 57,60,000 was discharged where applicable.

Adjustments on account of credit notes during the year totaled INR 48,00,000, resulting in tax reduction impact of INR 8,64,000.

Total net output tax liability determined for the year stood at INR 4,87,50,000.

2. Reverse Charge Obligations

The Company discharged tax under statutory reverse charge provisions amounting to INR 22,40,000, attributable primarily to:

Freight services: INR 13,90,000

Legal and professional services: INR 8,50,000

Accordingly, total gross tax obligation (including reverse charge) was INR 5,09,90,000.

3. Input Tax Credit Position

Eligible tax credits availed during the year were as follows:

On Raw Materials & Inputs: INR 2,18,75,000

On Input Services: INR 96,40,000

On Capital Goods: INR 54,25,000

Total credit availed aggregated to INR 3,69,40,000.

Out of the above, INR 3,69,40,000 was utilized towards output liability, and the balance tax paid in cash amounted to INR 1,18,10,000.

4. Reconciliation & Variance Analysis

Supplier-reported data reflected tax credit availability of INR 3,82,15,000, whereas credit availed stood at INR 3,69,40,000.

Variance identified: INR 12,75,000, categorized as:

Under vendor follow-up: INR 7,40,000

Provisionally reversed: INR 5,35,000

5. Interest, Fees & Refund Position

Interest paid on delayed tax remittance: INR 4,85,000

Statutory late fees: INR 1,20,000

Export-related refund claim submitted: INR 57,60,000

Refund sanctioned: INR 54,75,000

Refund pending: INR 2,85,000

6. Potential Exposure Assessment

In the event of adverse regulatory scrutiny, potential contingent exposure may include:

Credit disallowance risk: INR 12,75,000

Estimated interest exposure: INR 3,10,000

Estimated penalty exposure: INR 1,27,500

Compliance Overview

The Company demonstrated substantial indirect tax throughput with total taxable supplies of INR 21,95,00,000 and total tax liability of INR 4,87,50,000 during FY 2024–25. Primary compliance sensitivity arises from reconciliation variance of INR 12,75,000 and export refund exposure of INR 57,60,000.
"""

if __name__ == "__main__":
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        print("API Key not found!")
    else:
        parser = DocumentParser(api_key=API_KEY)
        print("[*] Running parser on GST Return text...")
        raw_extraction = parser.parse_financials(text)
        derived_features = parser.derive_risk_features(raw_extraction)
        
        final_result = {
            "company_financials": raw_extraction.get("company_financials", {}),
            "gst_behavioral_metrics": raw_extraction.get("gst_behavioral_metrics", {}),
            "document_risks": raw_extraction.get("document_risks", {}),
            "gst_risk_features": derived_features
        }
        
        print("\n========================================")
        print("EXTRACTED GST FINANCIAL JSON OUTPUT")
        print("========================================")
        print(json.dumps(final_result, indent=2))
