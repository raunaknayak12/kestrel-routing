"""
Production Training and Batch Inference Engine for Kestrel Home.

1. Refits the full feature pipeline + model on 100% of train rows (10,822 rows).
2. Serializes the production artifact to model.joblib.
3. Scores test_unlabelled.csv (2,178 rows).
4. Verifies formatting, row counts, and team names against sample_submission.csv.
5. Emits predictions.csv in the repo root.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression

from clean import load_and_clean_train, load_and_clean_test, VALID_TEAMS
from features import build_feature_pipeline

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT_DIR, "data")
MODEL_PATH = os.path.join(ROOT_DIR, "model.joblib")
PREDICTIONS_PATH = os.path.join(ROOT_DIR, "predictions.csv")
SAMPLE_SUBMISSION_PATH = os.path.join(DATA_DIR, "sample_submission.csv")

TRIAGE_THRESHOLD = 0.45


def train_and_export_model():
    print("=" * 60)
    print("KESTREL ROUTER: REFITTING PRODUCTION MODEL ON ALL DATA")
    print("=" * 60)

    train_path = os.path.join(DATA_DIR, "train.csv")
    res_path = os.path.join(DATA_DIR, "resolution_log.csv")
    
    print(f"Loading full training dataset from {train_path}...")
    df_all = load_and_clean_train(train_path, res_path)
    print(f"Total training samples: {len(df_all):,}")
    
    # Target distribution
    print("\nClass distribution in full training set:")
    print(df_all["final_team"].value_counts())
    
    print("\nConstructing production pipeline...")
    feature_pipe = build_feature_pipeline()
    prod_pipe = Pipeline([
        ("features", feature_pipe),
        ("clf", LogisticRegression(
            C=2.2,
            max_iter=2000,
            solver="lbfgs",
            random_state=42
        ))
    ])
    
    print("Fitting production pipeline on all 10,822 training requests...")
    prod_pipe.fit(df_all, df_all["final_team"])
    print("Training complete.")
    
    print(f"Exporting production model artifact to {MODEL_PATH}...")
    joblib.dump(prod_pipe, MODEL_PATH, compress=3)
    file_size_mb = os.path.getsize(MODEL_PATH) / (1024 * 1024)
    print(f"Model successfully saved! File size: {file_size_mb:.2f} MB")
    
    return prod_pipe


def generate_predictions(model):
    print("\n" + "=" * 60)
    print("SCORING UNLABELLED TEST DATASET")
    print("=" * 60)
    
    test_path = os.path.join(DATA_DIR, "test_unlabelled.csv")
    print(f"Loading test dataset from {test_path}...")
    test_df = load_and_clean_test(test_path)
    print(f"Total test requests to score: {len(test_df):,}")
    
    print("Predicting queues and calculating posterior probabilities...")
    preds = model.predict(test_df)
    probs = model.predict_proba(test_df)
    conf = np.max(probs, axis=1)
    
    test_df["predicted_team"] = preds
    test_df["confidence"] = conf
    test_df["needs_triage"] = conf < TRIAGE_THRESHOLD
    
    # Distribution of test predictions
    print("\nPredicted distribution across 7 teams on test set:")
    print(test_df["predicted_team"].value_counts())
    
    triaged_count = test_df["needs_triage"].sum()
    print(f"\nRequests flagged as 'needs_triage' (< {TRIAGE_THRESHOLD} conf): {triaged_count} ({triaged_count / len(test_df) * 100:.2f}%)")
    
    # Submission DataFrame matching exact schema: request_id, team
    sub = pd.DataFrame({
        "request_id": test_df["request_id"],
        "team": test_df["predicted_team"]
    })
    
    # Strict validation against sample_submission.csv
    print("\nValidating predictions against sample_submission.csv...")
    if os.path.exists(SAMPLE_SUBMISSION_PATH):
        sample_sub = pd.read_csv(SAMPLE_SUBMISSION_PATH)
        assert len(sub) == len(sample_sub), f"Row count mismatch: {len(sub)} vs {len(sample_sub)}"
        assert list(sub["request_id"]) == list(sample_sub["request_id"]), "Request ID order mismatch!"
        assert list(sub.columns) == ["request_id", "team"], f"Columns incorrect: {sub.columns}"
        print("  ✓ Row count matches (2,178 rows)")
        print("  ✓ Request ID order strictly matches sample_submission.csv")
    
    # Validate team names
    unique_teams = set(sub["team"].unique())
    invalid_teams = unique_teams - set(VALID_TEAMS)
    assert not invalid_teams, f"Invalid team names detected: {invalid_teams}"
    print(f"  ✓ All predicted teams belong to the valid 7 teams: {unique_teams}")
    
    # Check nulls
    assert sub["team"].isnull().sum() == 0, "Null values found in predictions!"
    print("  ✓ No null or empty predictions")
    
    sub.to_csv(PREDICTIONS_PATH, index=False)
    print(f"\n>>> predictions.csv written to {PREDICTIONS_PATH} ({os.path.getsize(PREDICTIONS_PATH):,} bytes)")
    
    return sub


if __name__ == "__main__":
    model = train_and_export_model()
    generate_predictions(model)
