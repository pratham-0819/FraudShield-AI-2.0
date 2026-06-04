class XAIEngine:
    def __init__(self):
        pass
    
    def explain(
        self,
        amount,
        location,
        device,
        time,
        usual_location=None,
        avg_amount=None,
        velocity_flag="PASS",
        geo_flag="LOW_RISK",
    ):
        explanations = {
            "behavior": "PASS",
            "location": "PASS",
            "device": "PASS",
            "velocity": "PASS"
        }
        
        # Behavior: if amount > 5x avg
        if avg_amount and amount > 5 * avg_amount:
            explanations["behavior"] = "ANOMALY"
        
        # Location: if mismatch
        if geo_flag in {"MEDIUM_RISK", "HIGH_RISK"}:
            explanations["location"] = "ANOMALY"
        
        # Device: if unknown
        if device.lower() == 'unknown':
            explanations["device"] = "ANOMALY"
        
        if velocity_flag == "HIGH_RISK":
            explanations["velocity"] = "ANOMALY"
        
        return explanations

    def build_narrative(self, model_explanation, rules, fraud_probability, action):
        reasons = []

        for item in model_explanation.get("top_risk_drivers", [])[:2]:
            reasons.append(
                f"{item['feature']} raised model risk by about {item['impact']:.2f}"
            )

        for rule_name, status in rules.items():
            if status == "ANOMALY":
                reasons.append(f"{rule_name} triggered an anomaly rule")

        if not reasons:
            reasons.append("the transaction closely matched the safer baseline profile")

        return (
            f"The transaction was marked {action.lower()} with an overall fraud "
            f"probability of {fraud_probability:.0%} because "
            + ", ".join(reasons[:3])
            + "."
        )
