"""
Training, Validation, and Evaluation Framework for Kestrel Home Service-Request Routing.

Implements:
1. Time-split validation (Train: Apr 2025–Mar 2026; Val: Apr–Jun 2026 CRM slice).
2. Evaluation of:
   - Majority class baseline
   - Legacy Bot benchmark
   - Keyword policy baseline
   - TF-IDF + Logistic Regression baseline
   - Engineered Full Pipeline (Word + Char TF-IDF + Domain Indicators + Metadata)
3. Cost-sensitive evaluation (Rs 305/transfer + Rs 260/contact = Rs 565/misroute).
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib

from clean import load_and_clean_train, VALID_TEAMS
from features import build_feature_pipeline
from baseline_rules import PolicyRuleRouter

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model.joblib")

# Economics from ops-policy §4
COST_PER_TRANSFER = 305
COST_PER_CONTACT = 260
TOTAL_MISROUTE_COST = COST_PER_TRANSFER + COST_PER_CONTACT  # Rs 565


def evaluate_predictions(y_true, y_pred, y_bot_label=None, model_name="Model"):
    """Calculate comprehensive evaluation metrics and rupee financial impact."""
    acc_final = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average="macro", labels=VALID_TEAMS)
    
    acc_bot = accuracy_score(y_bot_label, y_pred) if y_bot_label is not None else None
    
    # Financial calculation
    total_requests = len(y_true)
    misroutes = (y_true != y_pred).sum()
    misroute_rate = misroutes / total_requests
    incurred_cost = misroutes * TOTAL_MISROUTE_COST
    
    # Per-annum projection (based on ~7,200 requests/year)
    annual_volume = 7200
    annual_projected_cost = annual_volume * misroute_rate * TOTAL_MISROUTE_COST
    
    return {
        "model_name": model_name,
        "accuracy_vs_final": float(acc_final),
        "macro_f1_vs_final": float(f1_macro),
        "accuracy_vs_bot_label": float(acc_bot) if acc_bot is not None else None,
        "misroute_rate": float(misroute_rate),
        "val_misroutes": int(misroutes),
        "val_cost_incurred_rs": int(incurred_cost),
        "projected_annual_cost_rs": int(annual_projected_cost)
    }


def run_time_split_experiments():
    print("=" * 60)
    print("KESTREL HOME: TIME-SPLIT MODEL EXPERIMENTS & BENCHMARKS")
    print("=" * 60)
    
    train_path = os.path.join(DATA_DIR, "train.csv")
    res_path = os.path.join(DATA_DIR, "resolution_log.csv")
    
    print("1. Loading and cleaning dataset...")
    df = load_and_clean_train(train_path, res_path)
    print(f"   Total records: {len(df):,}")
    
    # Time split: Fit on Apr 2025 - Mar 2026, Validate on Apr - Jun 2026 (CRM only)
    split_date = pd.to_datetime("2026-04-01")
    train_df = df[df["created_at_ist"] < split_date].copy()
    val_df = df[df["created_at_ist"] >= split_date].copy()
    
    print(f"2. Time Split created:")
    print(f"   Train set: {len(train_df):,} rows ({train_df['created_at_ist'].min().date()} to {train_df['created_at_ist'].max().date()})")
    print(f"   Val set:   {len(val_df):,} rows ({val_df['created_at_ist'].min().date()} to {val_df['created_at_ist'].max().date()})")
    print(f"   Val set source distribution: {val_df['source'].value_counts().to_dict()}")
    
    y_val_final = val_df["final_team"].values
    y_val_bot = val_df["team_label"].values
    
    results = []
    
    # --- EXPERIMENT 1: Majority Class Router ---
    print("\n[Exp 1] Evaluating Majority Class Baseline (always Repairs)...")
    maj_pred = ["Repairs"] * len(val_df)
    res_maj = evaluate_predictions(y_val_final, maj_pred, y_val_bot, "Majority Class (Repairs)")
    results.append(res_maj)
    print(f"   Accuracy vs final_team: {res_maj['accuracy_vs_final']*100:.2f}% | Annual Cost: Rs {res_maj['projected_annual_cost_rs']:,}")
    
    # --- EXPERIMENT 2: Legacy Bot Benchmark ---
    print("\n[Exp 2] Evaluating Legacy Routing Bot Benchmark...")
    res_bot = evaluate_predictions(y_val_final, y_val_bot, y_val_bot, "Legacy Routing Bot")
    results.append(res_bot)
    print(f"   Accuracy vs final_team: {res_bot['accuracy_vs_final']*100:.2f}% | Annual Cost: Rs {res_bot['projected_annual_cost_rs']:,}")
    
    # --- EXPERIMENT 3: Policy-Derived Keyword Router ---
    print("\n[Exp 3] Evaluating Policy Keyword Rule Router...")
    router = PolicyRuleRouter()
    rule_pred = router.predict(val_df).values
    res_rule = evaluate_predictions(y_val_final, rule_pred, y_val_bot, "Policy Keyword Rules")
    results.append(res_rule)
    print(f"   Accuracy vs final_team: {res_rule['accuracy_vs_final']*100:.2f}% | Annual Cost: Rs {res_rule['projected_annual_cost_rs']:,}")
    
    # --- EXPERIMENT 4: Standard TF-IDF + Logistic Regression ---
    print("\n[Exp 4] Training Standard TF-IDF + Logistic Regression...")
    from sklearn.feature_extraction.text import TfidfVectorizer
    std_pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=10000)),
        ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=42))
    ])
    std_pipe.fit(train_df["clean_text"], train_df["final_team"])
    std_pred = std_pipe.predict(val_df["clean_text"])
    res_std = evaluate_predictions(y_val_final, std_pred, y_val_bot, "Standard TF-IDF + Logistic Regression")
    results.append(res_std)
    print(f"   Accuracy vs final_team: {res_std['accuracy_vs_final']*100:.2f}% | Annual Cost: Rs {res_std['projected_annual_cost_rs']:,}")
    
    # --- EXPERIMENT 5: Full Engineered Pipeline ---
    print("\n[Exp 5] Training Full Engineered Pipeline (Word+Char TF-IDF + Domain Features + Metadata)...")
    feature_pipe = build_feature_pipeline()
    full_pipe = Pipeline([
        ("features", feature_pipe),
        ("clf", LogisticRegression(C=2.5, max_iter=1500, class_weight="balanced", random_state=42))
    ])
    
    full_pipe.fit(train_df, train_df["final_team"])
    full_pred = full_pipe.predict(val_df)
    res_full = evaluate_predictions(y_val_final, full_pred, y_val_bot, "Engineered Feature Pipeline + Calibrated LR")
    results.append(res_full)
    print(f"   Accuracy vs final_team: {res_full['accuracy_vs_final']*100:.2f}% | Annual Cost: Rs {res_full['projected_annual_cost_rs']:,}")
    print(f"   Agreement with bot label: {res_full['accuracy_vs_bot_label']*100:.2f}%")
    
    # Print Detailed Classification Report
    print("\nDetailed Classification Report for Engineered Model:")
    print(classification_report(y_val_final, full_pred, digits=4))
    
    # Calculate savings vs bot
    bot_cost = res_bot["projected_annual_cost_rs"]
    model_cost = res_full["projected_annual_cost_rs"]
    annual_savings = bot_cost - model_cost
    print(f"\nFINANCIAL SAVINGS ESTIMATE:")
    print(f"   Bot Annual Misroute Cost:   Rs {bot_cost:,}")
    print(f"   Model Annual Misroute Cost: Rs {model_cost:,}")
    print(f"   Net Misroute Savings:       Rs {annual_savings:,} / year")
    print(f"   Plus Bot Licence Saved:     Rs 3,20,000 / year")
    print(f"   TOTAL ANNUAL BENEFIT:       Rs {annual_savings + 320000:,} / year")
    
    # Save experiment summary
    os.makedirs(REPORTS_DIR, exist_ok=True)
    summary_path = os.path.join(REPORTS_DIR, "validation_experiments.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nExperiment metrics saved to {summary_path}")
    
    return full_pipe, df


if __name__ == "__main__":
    run_time_split_experiments()
