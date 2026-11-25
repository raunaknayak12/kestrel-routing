"""
Unit tests for data cleaning, mojibake repair, and team queue normalization.
"""

import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from clean import repair_mojibake, clean_text, normalize_team_name, RENAME_MAP, VALID_TEAMS


def test_repair_mojibake_common_patterns():
    """Verify legacy Zoho UTF-8 CP1252 artifacts are properly repaired."""
    assert repair_mojibake("please help Ã¢â‚¬Â¦") == "please help ..."
    assert repair_mojibake("order KO260 Ã¢â‚¬â€œ delayed") == "order KO260 - delayed"
    assert repair_mojibake("urgÃ©nt: technician needed") == "urgent: technician needed"
    assert repair_mojibake("motor smÃ©ll") == "motor smell"


def test_clean_text_whitespace_and_empty():
    """Verify whitespace collapsing and empty/null handling."""
    assert clean_text("") == ""
    assert clean_text(None) == ""
    assert clean_text("   ") == ""
    assert clean_text("  hello \t\n world   ") == "hello world"
    assert clean_text("water purifier \r\n not working Ã¢â‚¬Â¦") == "water purifier not working ..."


def test_normalize_legacy_team_names():
    """Verify legacy team names are mapped to post-Jan-2026 standards per Policy §5."""
    assert normalize_team_name("Installations") == "Installs & Demo"
    assert normalize_team_name("Consumables") == "Filters & Consumables"
    assert normalize_team_name("  Installations  ") == "Installs & Demo"
    assert normalize_team_name("  Consumables  ") == "Filters & Consumables"


def test_normalize_standard_team_names_unchanged():
    """Verify current active 7 teams are unaffected by normalization."""
    for team in VALID_TEAMS:
        assert normalize_team_name(team) == team
