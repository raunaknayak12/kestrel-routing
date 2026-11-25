"""
Unit and Integration Test Suite for Kestrel Home Routing Service.
"""

import pytest
from fastapi.testclient import TestClient
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from app.main import app, VALID_TEAMS

client = TestClient(app)


def test_health_endpoint():
    """Verify service health endpoint status and metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert len(data["valid_teams"]) == 7


def test_route_repair_leak():
    """Verify hardware breakdown routes to Repairs."""
    payload = {
        "request_text": "water purifier leaking from bottom and display shows error code E2, please send technician",
        "product_family": "Water Purifier",
        "channel": "chat",
        "warranty_status": "in_warranty"
    }
    response = client.post("/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_team"] == "Repairs"
    assert data["confidence"] > 0.5
    assert data["needs_triage"] is False
    assert any("Repairs" in r or "fault" in r.lower() for r in data["reasons"])


def test_route_billing_dispute():
    """Verify genuine payment dispute routes to Billing."""
    payload = {
        "request_text": "amount deducted twice for invoice KO882190, please initiate refund of extra charge",
        "product_family": "Induction Cooktop",
        "channel": "email",
        "warranty_status": "out_of_warranty"
    }
    response = client.post("/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_team"] == "Billing"
    assert data["needs_triage"] is False


def test_policy_section_3_payment_trap():
    """
    Policy §3 test: Customer mentioning payment method in passing should NOT route to Billing.
    'paid via upi for installation visit' -> Installs & Demo or Repairs.
    """
    payload = {
        "request_text": "I already paid via UPI for new purifier installation visit, technician has not arrived yet",
        "product_family": "Water Purifier",
        "channel": "whatsapp",
        "warranty_status": "in_warranty"
    }
    response = client.post("/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_team"] != "Billing"
    assert data["predicted_team"] in ["Installs & Demo", "Repairs"]
    assert any("passing" in r.lower() or "not billing" in r.lower() for r in data["reasons"])


def test_vague_call_me_triage():
    """Verify vague short queries are flagged or evaluated honestly."""
    payload = {
        "request_text": "call me",
        "product_family": "Water Purifier",
        "channel": "ivr",
        "warranty_status": "in_warranty"
    }
    response = client.post("/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_team"] in VALID_TEAMS
    assert len(data["top3"]) == 3


def test_consumables_order():
    """Verify spares/filter replacement inquiries route to Filters & Consumables."""
    payload = {
        "request_text": "need to buy new carbon candle filter and sediment membrane cartridge for purifier",
        "product_family": "Water Purifier",
        "channel": "chat",
        "warranty_status": "in_warranty"
    }
    response = client.post("/route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_team"] == "Filters & Consumables"


def test_route_empty_request_text_fails():
    """Reject empty or whitespace-only requests with 422."""
    payload = {
        "request_text": "  ",
        "product_family": "Water Purifier",
        "channel": "chat",
        "warranty_status": "in_warranty"
    }
    response = client.post("/route", json=payload)
    assert response.status_code == 422


def test_route_oversize_request_text_fails():
    """Reject requests exceeding max length of 5000 characters with 422."""
    payload = {
        "request_text": "purifier fault " * 400,  # ~6000 chars
        "product_family": "Water Purifier",
        "channel": "chat",
        "warranty_status": "in_warranty"
    }
    response = client.post("/route", json=payload)
    assert response.status_code == 422


def test_route_invalid_channel_fails():
    """Reject invalid channel values with 422."""
    payload = {
        "request_text": "my purifier has broken down",
        "product_family": "Water Purifier",
        "channel": "carrier_pigeon",
        "warranty_status": "in_warranty"
    }
    response = client.post("/route", json=payload)
    assert response.status_code == 422


def test_route_invalid_product_family_fails():
    """Reject unknown product families with 422."""
    payload = {
        "request_text": "my appliance has broken down",
        "product_family": "Spaceship",
        "channel": "chat",
        "warranty_status": "in_warranty"
    }
    response = client.post("/route", json=payload)
    assert response.status_code == 422


def test_route_invalid_warranty_status_fails():
    """Reject invalid warranty status with 422."""
    payload = {
        "request_text": "my appliance has broken down",
        "product_family": "Water Purifier",
        "channel": "chat",
        "warranty_status": "lifetime_unlimited"
    }
    response = client.post("/route", json=payload)
    assert response.status_code == 422

