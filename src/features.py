"""
Feature Engineering Pipeline for Kestrel Home Service-Request Routing.

Combines:
1. Word-level TF-IDF (1-2 n-grams) on cleaned request text.
2. Character-level TF-IDF (3-5 n-grams) on cleaned request text for noise/phonetics tolerance.
3. One-hot encoding of categorical metadata: channel, product_family, warranty_status, source.
4. Domain indicator features addressing specific error traps:
   - Billing trap (payment dispute vs payment-in-passing)
   - Fault / breakdown indicators vs Spares/consumables
   - Installation / demo triggers
   - Vague query / triage flags
"""

import re
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline, FeatureUnion


class DomainHeuristicFeatures(BaseEstimator, TransformerMixin):
    """
    Extracts high-signal domain interaction flags designed from operations policy
    and failure analysis.
    """
    
    PAYMENT_DISPUTE_WORDS = r"\b(invoice|bill|gst|double\s*charge|deducted|refund|emi|coupon|extra\s*charge|receipt|statement)\b"
    PAYMENT_MENTION_WORDS = r"\b(paid|upi|card|gpay|google\s*pay|paytm|phonepe|net\s*banking|cash)\b"
    FAULT_WORDS = r"\b(fault|not\s*working|broke|broken|breakdown|leak|leaking|noise|smell|burnt|smoke|trip|tripping|mcb|error|e\d+|beeping|shaking|vibrating|damaged)\b"
    CONSUMABLE_WORDS = r"\b(filter|filters|candle|candles|membrane|amc|jar|jars|blade|blades|spare|spares|brush|brushes|cartridge)\b"
    INSTALL_WORDS = r"\b(install|installation|demo|wall\s*mount|mounting|unboxing|setup|fitting|fit|new\s*product)\b"
    WARRANTY_WORDS = r"\b(warranty|shield|coverage|extended\s*warranty|certificate|validity|register|registration)\b"
    RETURN_WORDS = r"\b(return|replacement|replace|wrong\s*product|wrong\s*item|incomplete|missing\s*part|box\s*empty|exchange)\b"
    VAGUE_WORDS = r"\b(call\s*me|call\s*back|pls\s*call|please\s*call|contact\s*me|assist|help\s*me)\b"

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        X can be a DataFrame or list/Series of texts.
        Returns a 2D numpy array of domain binary/ratio flags.
        """
        if isinstance(X, pd.DataFrame):
            texts = X["clean_text"].fillna("").astype(str).values
        elif isinstance(X, pd.Series):
            texts = X.fillna("").astype(str).values
        else:
            texts = [str(x) for x in X]

        features = []
        for text in texts:
            t_lower = text.lower()
            
            has_pay_dispute = int(bool(re.search(self.PAYMENT_DISPUTE_WORDS, t_lower)))
            has_pay_mention = int(bool(re.search(self.PAYMENT_MENTION_WORDS, t_lower)))
            
            # Key Policy §3 discriminator: True payment problem vs paid-in-passing
            genuine_billing_signal = int(has_pay_dispute and has_pay_mention)
            paid_in_passing_signal = int(has_pay_mention and not has_pay_dispute)
            
            has_fault = int(bool(re.search(self.FAULT_WORDS, t_lower)))
            has_consumable = int(bool(re.search(self.CONSUMABLE_WORDS, t_lower)))
            has_install = int(bool(re.search(self.INSTALL_WORDS, t_lower)))
            has_warranty = int(bool(re.search(self.WARRANTY_WORDS, t_lower)))
            has_return = int(bool(re.search(self.RETURN_WORDS, t_lower)))
            has_vague = int(bool(re.search(self.VAGUE_WORDS, t_lower)))
            
            # Purifier breakdown vs filter replacement distinction
            purifier_fault = int("purifier" in t_lower and has_fault)
            purifier_filter = int("purifier" in t_lower and has_consumable and not has_fault)
            
            # Text length properties
            word_count = len(t_lower.split())
            is_very_short = int(word_count <= 4)
            
            features.append([
                has_pay_dispute,
                has_pay_mention,
                genuine_billing_signal,
                paid_in_passing_signal,
                has_fault,
                has_consumable,
                has_install,
                has_warranty,
                has_return,
                has_vague,
                purifier_fault,
                purifier_filter,
                word_count,
                is_very_short
            ])
            
        return np.array(features, dtype=np.float32)


def build_feature_pipeline() -> ColumnTransformer:
    """
    Constructs an end-to-end scikit-learn ColumnTransformer combining:
    - Word-level TF-IDF
    - Char-level TF-IDF
    - Domain heuristics
    - Categorical One-Hot Encodings
    """
    # Word TF-IDF
    word_tfidf = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=12000,
        sublinear_tf=True,
        min_df=2
    )
    
    # Char TF-IDF for robust matching on IVR audio phonetic noise & typos
    char_tfidf = TfidfVectorizer(
        analyzer="char",
        ngram_range=(3, 5),
        max_features=15000,
        sublinear_tf=True,
        min_df=3
    )
    
    # Text pipeline combining word, char, and domain indicators
    text_features = FeatureUnion([
        ("word_tfidf", word_tfidf),
        ("char_tfidf", char_tfidf),
        ("domain_heuristics", DomainHeuristicFeatures())
    ])
    
    # Categorical encoder
    cat_encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=True)
    
    transformer = ColumnTransformer(
        transformers=[
            ("text", text_features, "clean_text"),
            ("cat", cat_encoder, ["channel", "product_family", "warranty_status"])
        ],
        remainder="drop"
    )
    
    return transformer


if __name__ == "__main__":
    from clean import clean_text
    
    sample_df = pd.DataFrame([{
        "clean_text": clean_text("paid via upi for water purifier installation but technician did not arrive"),
        "channel": "whatsapp",
        "product_family": "Water Purifier",
        "warranty_status": "in_warranty"
    }])
    
    pipeline = build_feature_pipeline()
    X = pipeline.fit_transform(sample_df)
    print("Extracted feature matrix shape:", X.shape)
    
    dh = DomainHeuristicFeatures()
    print("Domain heuristics output:", dh.transform(sample_df["clean_text"]))
