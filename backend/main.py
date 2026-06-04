from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
# import os
# import sys
# sys.path.append(os.path.dirname(__file__))

from .model.train_model import train_models
from .services.fraud_engine import FraudEngine
from .services.heuristic_engine import HeuristicEngine
from .services.xai_engine import XAIEngine
from .services.behavior_engine import BehaviorEngine
from .services.graph_engine import GraphEngine
from .services.geo_engine import GeoEngine
from .database.db import get_db, create_tables
from .database.models import Transaction

app = FastAPI(title="FraudShield AI", description="Production-level fintech fraud detection system")

# Initialize engines
fraud_engine = FraudEngine()
heuristic_engine = HeuristicEngine()
xai_engine = XAIEngine()
behavior_engine = BehaviorEngine()
graph_engine = GraphEngine()
geo_engine = GeoEngine()

# Train models if not exist
train_models()

class SimulateRequest(BaseModel):
    sender: str
    receiver: str
    amount: float
    age: int
    location: str
    device: str
    time: str
    scenario: str
    policy_strictness: int  # 1-10

@app.on_event("startup")
def startup_event():
    create_tables()

@app.post("/simulate")
def simulate_transaction(request: SimulateRequest, db: Session = Depends(get_db)):
    # Extract data
    sender = request.sender
    receiver = request.receiver
    amount = request.amount
    age = request.age
    location = request.location
    device = request.device
    time = request.time
    scenario = request.scenario
    policy_strictness = request.policy_strictness
    
    city_pop = 100000  # assume
    hour = int(time.split(':')[0]) if ':' in time else 12
    
    # ML prediction
    features = [amount, hour, age, city_pop]
    model_fraud_prob = fraud_engine.predict_fraud_probability(features)
    model_explanation = fraud_engine.explain_prediction(features)
    
    # Heuristic score
    heuristic_score = heuristic_engine.calculate_score(amount, time, device, scenario)
    heuristic_prob = heuristic_engine.estimate_probability(amount, time, device, scenario)
    
    # Behavior and velocity are evaluated against prior history first.
    avg_amount = behavior_engine.get_average(sender)
    behavior_flag = behavior_engine.check_anomaly(sender, amount)
    behavior_engine.add_transaction(sender, amount, datetime.utcnow())
    velocity_flag = behavior_engine.check_velocity(sender)
    
    # Graph
    graph_engine.add_transaction(sender, receiver)
    graph_flag = graph_engine.check_risk(sender)
    
    transaction_timestamp = datetime.utcnow()
    geo_result = geo_engine.assess_location(db, sender, location, time)
    geo_flag = geo_result["flag"]
    
    # XAI explanations
    xai = xai_engine.explain(
        amount,
        location,
        device,
        time,
        location,
        avg_amount,
        velocity_flag,
        geo_flag,
    )
    
    # Risk breakdown
    risk_breakdown = {
        "behavior": 20 if behavior_flag == "ANOMALY" else 0,
        "location": 25 if geo_flag == "HIGH_RISK" else 10 if geo_flag == "MEDIUM_RISK" else 0,
        "device": 20 if device.lower() == 'unknown' else 0,
        "velocity": 20 if velocity_flag == "HIGH_RISK" else 0,
    }

    # Calibrate the raw model score with contextual heuristics so
    # moderately unusual transactions do not inherit the full model spike
    # when the surrounding signals still look normal.
    fraud_prob = (model_fraud_prob * 0.35) + (heuristic_prob * 0.65)
    if behavior_flag == "ANOMALY":
        fraud_prob += 0.15
    if geo_flag == "HIGH_RISK":
        fraud_prob += 0.18
    elif geo_flag == "MEDIUM_RISK":
        fraud_prob += 0.06
    if velocity_flag == "HIGH_RISK":
        fraud_prob += 0.08

    fraud_prob = min(0.99, fraud_prob)
    
    raw_signal_score = heuristic_score + sum(risk_breakdown.values())
    normalized_signal_score = min(100, round((raw_signal_score / 240) * 100))
    risk_score = min(
        100,
        round((fraud_prob * 100 * 0.6) + (normalized_signal_score * 0.4)),
    )
    
    # Flags
    flags = {
        "behavior": behavior_flag,
        "graph": graph_flag,
        "geo": geo_flag,
        "velocity": velocity_flag,
    }

    # Action criteria
    allow_threshold = 25 + policy_strictness * 1.5
    suspicious_threshold = 45 + policy_strictness * 2
    block_threshold = 70 + policy_strictness * 2.5

    strong_signal_count = sum(
        [
            behavior_flag == "ANOMALY",
            geo_flag == "HIGH_RISK",
            velocity_flag == "HIGH_RISK",
            graph_flag == "HIGH_RISK",
            device.lower() == "unknown",
        ]
    )

    if (
        fraud_prob >= 0.85
        or strong_signal_count >= 2
        or (risk_score >= block_threshold and fraud_prob >= 0.55)
        or (fraud_prob >= 0.70 and risk_score >= 65)
    ):
        action = "BLOCK"
    elif (
        risk_score >= suspicious_threshold
        or fraud_prob >= 0.30
        or geo_flag == "MEDIUM_RISK"
        or risk_score >= allow_threshold
    ):
        action = "SUSPICIOUS"
    else:
        action = "ALLOW"
    
    # Advanced explanation
    advanced_explanation = fraud_engine.get_feature_importances()
    xai_narrative = xai_engine.build_narrative(
        model_explanation,
        xai,
        fraud_prob,
        action,
    )
    
    # Summary
    summary = (
        f"Transaction from {sender} to {receiver} for ${amount}. "
        f"Risk score: {risk_score}. Action: {action}."
    )
    
    # Save to DB
    transaction = Transaction(amount=amount, risk_score=risk_score, action=action)
    transaction.sender = sender
    transaction.location = location
    transaction.event_time = transaction_timestamp
    db.add(transaction)
    db.commit()
    
    return {
        "risk_score": risk_score,
        "action": action,
        "fraud_probability": fraud_prob,
        "model_probability": model_fraud_prob,
        "xai": xai,
        "model_explanation": {
            **model_explanation,
            "narrative": xai_narrative,
        },
        "advanced_explanation": advanced_explanation,
        "flags": flags,
        "geo_details": geo_result,
        "risk_breakdown": risk_breakdown,
        "summary": summary
    }
