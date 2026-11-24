"""
Data Cleaning and Normalization Module for Kestrel Home Service Requests.

Handles:
1. Repair of Mojibake encoding artifacts from legacy Zoho Desk exports.
2. Queue name standardization (mapping legacy names to modern post-Jan-2026 names).
3. Text cleaning, whitespace normalization, and punctuation standardization.
4. Handling missing values and data integrity validation.
"""

import re
import pandas as pd

# Mapping historical team names to active standard names per Policy §5
RENAME_MAP = {
    "Installations": "Installs & Demo",
    "Consumables": "Filters & Consumables"
}

VALID_TEAMS = [
    "Installs & Demo",
    "Repairs",
    "Filters & Consumables",
    "Billing",
    "Returns & Replacement",
    "Warranty Claims",
    "Product Advice"
]

# Explicit mapping of double-encoded and single-encoded UTF-8 artifacts in Zoho Desk
MOJIBAKE_REPLACEMENTS = [
    ("Ã¢â‚¬Â¦", "..."),
    ("â€¦", "..."),
    ("Ã¢â‚¬â€œ", "-"),
    ("â€“", "-"),
    ("Ã¢â‚¬â„¢", "'"),
    ("â€™", "'"),
    ("Ã¢â‚¬Å“", '"'),
    ("â€œ", '"'),
    ("Ã¢â‚¬Â", '"'),
    ("â€", '"'),
    ("Ã©", "e"),
    ("Ã¨", "e"),
    ("Ã ", "a"),
    ("Ã¡", "a"),
    ("Ã³", "o"),
    ("Ãº", "u"),
    ("Ã±", "n"),
    ("Â", " "),
]


def repair_mojibake(text: str) -> str:
    """Repair corrupted encoding artifacts in text strings."""
    if not isinstance(text, str):
        return ""
    
    # Apply explicit replacements
    for pattern, replacement in MOJIBAKE_REPLACEMENTS:
        text = text.replace(pattern, replacement)
    
    # Remove remaining orphaned control/high-byte remnants if any
    text = re.sub(r"[\x80-\x9f]", " ", text)
    return text


def clean_text(text: str) -> str:
    """Standardize text by repairing encoding, stripping extra whitespace, and lowercasing."""
    if not isinstance(text, str) or not text.strip():
        return ""
    
    text = repair_mojibake(text)
    # Replace non-breaking spaces or tabs with regular space
    text = re.sub(r"[\r\n\t]+", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_team_name(team: str) -> str:
    """Map any legacy team name to the active standardized name."""
    if not isinstance(team, str):
        return team
    return RENAME_MAP.get(team.strip(), team.strip())


def load_and_clean_train(train_path: str, resolution_log_path: str) -> pd.DataFrame:
    """
    Load train.csv and resolution_log.csv, merge them, clean text,
    and normalize team names.
    """
    train = pd.read_csv(train_path)
    res = pd.read_csv(resolution_log_path)
    
    df = pd.merge(train, res, on="request_id")
    
    # Clean text
    df["clean_text"] = df["request_text"].fillna("").apply(clean_text)
    
    # Normalize team queues
    df["team_label"] = df["team_label"].apply(normalize_team_name)
    df["first_team"] = df["first_team"].apply(normalize_team_name)
    df["final_team"] = df["final_team"].apply(normalize_team_name)
    
    # Date parsing
    df["created_at_ist"] = pd.to_datetime(df["created_at_ist"])
    
    return df


def load_and_clean_test(test_path: str) -> pd.DataFrame:
    """
    Load test_unlabelled.csv and clean text fields.
    """
    df = pd.read_csv(test_path)
    df["clean_text"] = df["request_text"].fillna("").apply(clean_text)
    df["created_at_ist"] = pd.to_datetime(df["created_at_ist"])
    return df


if __name__ == "__main__":
    import os
    base_dir = os.path.dirname(__file__)
    sample = "urgÃ©nt: installer did not turn up for room heater asap Ã¢â‚¬Â¦"
    print("Before:", sample)
    print("After: ", clean_text(sample))
