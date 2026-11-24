"""
Kestrel Home Service-Request Routing Service.

FastAPI Application providing:
1. POST /route - Intelligent request classification with explanation reasons and triage detection.
2. GET /health - Service health and model status check.
3. Interactive UI served at root URL (/).
"""

import os
import sys
import re
import joblib
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Ensure src is on python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from clean import clean_text, VALID_TEAMS

MODEL_PATH = os.path.join(ROOT_DIR, "model.joblib")
TRIAGE_THRESHOLD = 0.45

app = FastAPI(
    title="Kestrel Home Service Routing API",
    description="Intelligent, zero-cost offline routing service for inbound customer requests.",
    version="1.0.0"
)

# Load model artifact
model = None

def get_model():
    global model
    if model is None:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
    return model

# Eagerly attempt to load model at import time
get_model()

@app.get("/health")
def health_check():
    """Health check endpoint validating model status."""
    m = get_model()
    return {
        "status": "ok",
        "model_loaded": m is not None,
        "valid_teams": VALID_TEAMS,
        "triage_threshold": TRIAGE_THRESHOLD,
        "runtime_cost_per_request": "Rs 0.00 (Offline Classical Model)"
    }


class ServiceRequest(BaseModel):
    request_text: str = Field(..., description="Customer opening message or IVR transcript")
    channel: str = Field(default="chat", description="Channel: ivr, chat, whatsapp, or email")
    product_family: str = Field(default="Water Purifier", description="Product line")
    warranty_status: str = Field(default="in_warranty", description="in_warranty, shield, or out_of_warranty")
    source: Optional[str] = Field(default="crm", description="Source system: crm or legacy_zoho")


class AlternativePrediction(BaseModel):
    team: str
    confidence: float


class RouteResponse(BaseModel):
    predicted_team: str
    confidence: float
    needs_triage: bool
    top3: List[AlternativePrediction]
    reasons: List[str]


def generate_routing_explanations(text: str, predicted_team: str, confidence: float, product: str) -> List[str]:
    """Generate plain-English diagnostic explanations for customer service agents."""
    reasons = []
    t_lower = text.lower()
    
    # Billing Trap check (Policy §3)
    has_pay_method = bool(re.search(r"\b(paid|upi|card|gpay|google\s*pay|paytm|phonepe|net\s*banking|cash)\b", t_lower))
    has_pay_dispute = bool(re.search(r"\b(invoice|bill|gst|double\s*charge|deducted|refund|emi|coupon|extra\s*charge)\b", t_lower))
    
    if has_pay_method and not has_pay_dispute:
        reasons.append("Customer mentioned payment method in passing (Policy §3: not Billing unless payment itself is disputed).")
    elif has_pay_dispute:
        reasons.append("Detected payment/invoice dispute terminology ('invoice/refund/double charge/emi') → Billing queue.")

    # Fault triggers
    fault_matches = re.findall(r"\b(error\s*\w+|leak\w*|noise|burnt|smell|trip\w*|mcb|not\s*working|broke\w*|breakdown|spark|vibrat\w*)\b", t_lower)
    if fault_matches:
        reasons.append(f"Detected physical fault indicators: {', '.join(set(fault_matches))} → Hardware diagnostic / Repairs.")

    # Spares triggers
    spares_matches = re.findall(r"\b(filter\w*|candle\w*|membrane\w*|amc|jar\w*|blade\w*|spares?|cartridge)\b", t_lower)
    if spares_matches:
        if not fault_matches:
            reasons.append(f"Identified routine consumable / spare part inquiry: {', '.join(set(spares_matches))} → Filters & Consumables.")
        else:
            reasons.append(f"Consumable keyword present with active fault symptoms → prioritized Repairs.")

    # Installation / Demo
    install_matches = re.findall(r"\b(install\w*|demo\w*|wall\s*mount\w*|unboxing|setup|fitting)\b", t_lower)
    if install_matches:
        reasons.append(f"New product onboarding / installation keywords: {', '.join(set(install_matches))} → Installs & Demo.")

    # Returns
    return_matches = re.findall(r"\b(return\w*|replace\w*|damaged|wrong\s*item|missing\s*part|exchange)\b", t_lower)
    if return_matches:
        reasons.append(f"Fulfillment / delivery anomaly keywords: {', '.join(set(return_matches))} → Returns & Replacement.")

    # Warranty
    warranty_matches = re.findall(r"\b(warranty|shield|certificate|coverage|claim\s*status)\b", t_lower)
    if warranty_matches:
        reasons.append(f"Warranty / Kestrel Shield coverage question: {', '.join(set(warranty_matches))} → Warranty Claims.")

    # Advice
    advice_matches = re.findall(r"\b(how\s*to\s*use|clean\w*|manual|guide|instruction|recipe|specification)\b", t_lower)
    if advice_matches:
        reasons.append(f"Usage / guidance question: {', '.join(set(advice_matches))} → Product Advice.")

    # Vague inquiry
    if re.search(r"\b(call\s*me|call\s*back|pls\s*call|contact\s*me)\b", t_lower):
        reasons.append("Contains generic 'call me' request without technical context.")

    if confidence < TRIAGE_THRESHOLD:
        reasons.append(f"Low confidence ({confidence*100:.1f}% < {TRIAGE_THRESHOLD*100:.0f}% threshold) → Flagged for human triage.")
    else:
        reasons.append(f"High-confidence match ({confidence*100:.1f}%) for queue: {predicted_team}.")

    return reasons


@app.get("/health")
def health_check():
    """Health check endpoint validating model status."""
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "valid_teams": VALID_TEAMS,
        "triage_threshold": TRIAGE_THRESHOLD,
        "runtime_cost_per_request": "Rs 0.00 (Offline Classical Model)"
    }


@app.post("/route", response_model=RouteResponse)
def route_service_request(req: ServiceRequest):
    """
    Route an inbound service request to the optimal queue with explanation.
    """
    m = get_model()
    if m is None:
        raise HTTPException(status_code=503, detail="Routing model artifact not found.")

    clean_t = clean_text(req.request_text)
    
    input_df = pd.DataFrame([{
        "clean_text": clean_t,
        "channel": req.channel,
        "product_family": req.product_family,
        "warranty_status": req.warranty_status,
        "source": req.source or "crm"
    }])
    
    probs = m.predict_proba(input_df)[0]
    classes = list(m.classes_)
    
    # Sort top 3
    sorted_indices = np.argsort(probs)[::-1]
    top_team = classes[sorted_indices[0]]
    top_conf = float(probs[sorted_indices[0]])
    
    top3 = [
        AlternativePrediction(team=classes[idx], confidence=round(float(probs[idx]), 4))
        for idx in sorted_indices[:3]
    ]
    
    needs_triage = top_conf < TRIAGE_THRESHOLD
    reasons = generate_routing_explanations(req.request_text, top_team, top_conf, req.product_family)
    
    return RouteResponse(
        predicted_team=top_team,
        confidence=round(top_conf, 4),
        needs_triage=needs_triage,
        top3=top3,
        reasons=reasons
    )


# Serve static web UI
static_dir = os.path.join(CURRENT_DIR, "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(CURRENT_DIR, "static", "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Kestrel Routing Service API. Visit /docs for interactive Swagger API documentation."}
