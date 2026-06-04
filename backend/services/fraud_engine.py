import joblib
from copy import deepcopy
from pathlib import Path


class FraudEngine:
    def __init__(self):
        self.fraud_model = None
        self.creditcard_model = None
        self.feature_names = ['amt', 'hour', 'age', 'city_pop']
        self.reference_profile = {
            'amt': 50.0,
            'hour': 14.0,
            'age': 35.0,
            'city_pop': 100000.0,
        }
        self.load_models()
    
    def load_models(self):
        backend_root = Path(__file__).resolve().parent.parent
        project_root = backend_root.parent

        fraud_candidates = [
            backend_root / 'fraud_model.pkl',
            project_root / 'fraud_model.pkl',
        ]
        creditcard_candidates = [
            backend_root / 'creditcard_model.pkl',
            project_root / 'creditcard_model.pkl',
        ]

        for fraud_path in fraud_candidates:
            if fraud_path.exists():
                self.fraud_model = joblib.load(fraud_path)
                break

        for creditcard_path in creditcard_candidates:
            if creditcard_path.exists():
                self.creditcard_model = joblib.load(creditcard_path)
                break
    
    def predict_fraud_probability(self, features):
        # For simplicity, use fraud_model if available, else assume 0
        if self.fraud_model:
            # features should be [amt, hour, age, city_pop]
            pred = self.fraud_model.predict_proba([features])[:, 1][0]
            return float(pred)
        return 0.0

    def explain_prediction(self, features):
        if not self.fraud_model:
            return {
                "base_probability": 0.0,
                "top_risk_drivers": [],
                "top_protective_factors": [],
            }

        actual_probability = self.predict_fraud_probability(features)
        contributions = []

        for index, feature_name in enumerate(self.feature_names):
            comparison_features = deepcopy(features)
            comparison_features[index] = self.reference_profile[feature_name]
            comparison_probability = self.predict_fraud_probability(comparison_features)
            delta = actual_probability - comparison_probability

            contributions.append(
                {
                    "feature": feature_name,
                    "impact": round(delta, 4),
                    "actual_value": float(features[index]),
                    "reference_value": float(self.reference_profile[feature_name]),
                }
            )

        risk_drivers = [
            {
                **item,
                "direction": "increase",
            }
            for item in sorted(
                [contribution for contribution in contributions if contribution["impact"] > 0],
                key=lambda contribution: contribution["impact"],
                reverse=True,
            )[:3]
        ]
        protective_factors = [
            {
                **item,
                "direction": "decrease",
            }
            for item in sorted(
                [contribution for contribution in contributions if contribution["impact"] < 0],
                key=lambda contribution: contribution["impact"],
            )[:3]
        ]

        return {
            "base_probability": round(actual_probability, 4),
            "top_risk_drivers": risk_drivers,
            "top_protective_factors": protective_factors,
        }
    
    def get_feature_importances(self):
        if self.fraud_model:
            return {
                key: float(value)
                for key, value in zip(
                    ['amt', 'hour', 'age', 'city_pop'],
                    self.fraud_model.feature_importances_,
                )
            }
        return {}
