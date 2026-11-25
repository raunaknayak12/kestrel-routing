"""
Unit tests for domain feature extraction and feature engineering pipeline.
"""

import pytest
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from features import DomainHeuristicFeatures, build_feature_pipeline


def test_domain_features_payment_trap():
    """
    Policy §3: Customer mentions payment method in passing (UPI) without billing dispute
    must yield paid_in_passing_signal=1, genuine_billing_signal=0.
    """
    dh = DomainHeuristicFeatures()
    
    # 1. Payment in passing
    feats_passing = dh.transform(["I paid via UPI for water purifier installation"])[0]
    has_pay_dispute, has_pay_mention, genuine_billing, paid_in_passing = feats_passing[:4]
    assert has_pay_mention == 1.0
    assert has_pay_dispute == 0.0
    assert genuine_billing == 0.0
    assert paid_in_passing == 1.0
    
    # 2. Genuine billing dispute
    feats_dispute = dh.transform(["amount deducted twice for invoice, request refund of extra charge"])[0]
    has_pay_dispute2, has_pay_mention2, genuine_billing2, paid_in_passing2 = feats_dispute[:4]
    assert has_pay_dispute2 == 1.0
    assert genuine_billing2 == 0.0  # mentions dispute but not payment method
    
    # 3. Genuine billing with payment method
    feats_both = dh.transform(["paid via UPI but amount deducted twice on invoice, refund needed"])[0]
    has_pay_dispute3, has_pay_mention3, genuine_billing3, paid_in_passing3 = feats_both[:4]
    assert has_pay_mention3 == 1.0
    assert has_pay_dispute3 == 1.0
    assert genuine_billing3 == 1.0
    assert paid_in_passing3 == 0.0


def test_domain_features_fault_vs_consumables():
    """Verify fault vs consumable indicators and purifier breakdown discrimination."""
    dh = DomainHeuristicFeatures()
    
    # Purifier fault
    feats_fault = dh.transform(["water purifier leaking from bottom, error code E2"])[0]
    has_fault = feats_fault[4]
    has_consumable = feats_fault[5]
    purifier_fault = feats_fault[10]
    purifier_filter = feats_fault[11]
    assert has_fault == 1.0
    assert purifier_fault == 1.0
    assert purifier_filter == 0.0
    
    # Routine consumable replacement
    feats_filter = dh.transform(["need replacement sediment candle filter and carbon membrane for purifier"])[0]
    has_fault2 = feats_filter[4]
    has_consumable2 = feats_filter[5]
    purifier_fault2 = feats_filter[10]
    purifier_filter2 = feats_filter[11]
    assert has_consumable2 == 1.0
    assert has_fault2 == 0.0
    assert purifier_filter2 == 1.0
    assert purifier_fault2 == 0.0


def test_domain_features_vague_call_me():
    """Verify vague short queries trigger vague flag and very short indicator."""
    dh = DomainHeuristicFeatures()
    feats = dh.transform(["please call me urgently"])[0]
    has_vague = feats[9]
    is_very_short = feats[13]
    assert has_vague == 1.0
    assert is_very_short == 1.0


def test_feature_pipeline_fit_transform():
    """Verify ColumnTransformer end-to-end fit and transform on DataFrame."""
    df = pd.DataFrame([
        {
            "clean_text": "water purifier leaking water from bottom",
            "channel": "chat",
            "product_family": "Water Purifier",
            "warranty_status": "in_warranty"
        },
        {
            "clean_text": "water purifier not working leaking filter",
            "channel": "whatsapp",
            "product_family": "Water Purifier",
            "warranty_status": "in_warranty"
        },
        {
            "clean_text": "water purifier filter replacement needed",
            "channel": "chat",
            "product_family": "Water Purifier",
            "warranty_status": "shield"
        },
        {
            "clean_text": "refund of duplicate invoice deduction",
            "channel": "email",
            "product_family": "Induction Cooktop",
            "warranty_status": "out_of_warranty"
        }
    ])
    pipeline = build_feature_pipeline()
    X = pipeline.fit_transform(df)
    assert X.shape[0] == 4
    assert X.shape[1] > 20
