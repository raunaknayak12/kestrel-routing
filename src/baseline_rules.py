"""
Heuristic Keyword Baseline and Benchmark for Kestrel Home Service Requests.

Implements:
1. Majority Class Router (always predict Repairs).
2. Bot benchmark evaluation.
3. Policy-derived Keyword Rule Router based directly on ops-policy.pdf §3 and teams.csv.
"""

import re
import pandas as pd
from typing import Dict, Any

VALID_TEAMS = [
    "Installs & Demo",
    "Repairs",
    "Filters & Consumables",
    "Billing",
    "Returns & Replacement",
    "Warranty Claims",
    "Product Advice"
]

class PolicyRuleRouter:
    """
    Keyword-based routing engine translating operations policy §3 directly into rules.
    Serves as an explainable sanity-floor baseline.
    """

    # High precision keyword sets
    BILLING_KEYWORDS = r"\b(invoice|bill|gst|double\s*charge|charged\s*twice|refund|emi|coupon|extra\s*deduction|payment\s*deducted|transaction\s*failed)\b"
    RETURNS_KEYWORDS = r"\b(return|replace|damaged\s*delivery|wrong\s*product|wrong\s*item|missing\s*part|box\s*empty|exchange|broken\s*seal)\b"
    INSTALL_KEYWORDS = r"\b(install|installation|demo|wall\s*mount|mounting|unboxing|setup|fitting|fit|technician\s*visit\s*for\s*demo)\b"
    CONSUMABLE_KEYWORDS = r"\b(filter|candle|membrane|amc\s*kit|spare\s*jar|blade|spares|carbon\s*filter|sediment|cartridge)\b"
    WARRANTY_KEYWORDS = r"\b(warranty|shield|kestrel\s*shield|claim\s*status|warranty\s*certificate|coverage|register\s*warranty|warranty\s*period)\b"
    ADVICE_KEYWORDS = r"\b(how\s*to\s*use|user\s*manual|recipe|guide|cleaning\s*instruction|specification|capacity|features)\b"
    REPAIR_KEYWORDS = r"\b(not\s*working|fault|leak|leaking|noise|burnt|tripping|mcb|error|beeping|spark|smoke|stopped\s*working|breakdown|vibration)\b"

    def predict_one(self, text: str, product: str = "", warranty: str = "") -> str:
        text_lower = text.lower() if isinstance(text, str) else ""

        # Policy §3: Billing ONLY when payment itself is the problem
        if re.search(self.BILLING_KEYWORDS, text_lower):
            return "Billing"

        # Returns & Replacement within return window
        if re.search(self.RETURNS_KEYWORDS, text_lower):
            return "Returns & Replacement"

        # Warranty registration / coverage questions
        if re.search(self.WARRANTY_KEYWORDS, text_lower) and not re.search(self.REPAIR_KEYWORDS, text_lower):
            return "Warranty Claims"

        # Spares & Consumables (only if not a device breakdown)
        if re.search(self.CONSUMABLE_KEYWORDS, text_lower) and not re.search(self.REPAIR_KEYWORDS, text_lower):
            return "Filters & Consumables"

        # Installation & Demo
        if re.search(self.INSTALL_KEYWORDS, text_lower) and not re.search(self.REPAIR_KEYWORDS, text_lower):
            return "Installs & Demo"

        # Product Advice (no fault reported)
        if re.search(self.ADVICE_KEYWORDS, text_lower) and not re.search(self.REPAIR_KEYWORDS, text_lower):
            return "Product Advice"

        # Product faults / repairs
        if re.search(self.REPAIR_KEYWORDS, text_lower):
            return "Repairs"

        # Fallback to majority class
        return "Repairs"

    def predict(self, df: pd.DataFrame) -> pd.Series:
        return df["clean_text"].apply(self.predict_one)
