from datetime import datetime, timedelta


class BehaviorEngine:
    def __init__(self):
        self.user_history = {}  # user: list of {amount, timestamp}
    
    def add_transaction(self, user, amount, timestamp=None):
        if user not in self.user_history:
            self.user_history[user] = []
        self.user_history[user].append(
            {
                "amount": amount,
                "timestamp": timestamp or datetime.utcnow(),
            }
        )
    
    def get_average(self, user):
        if user in self.user_history and self.user_history[user]:
            amounts = [entry["amount"] for entry in self.user_history[user]]
            return sum(amounts) / len(amounts)
        return None
    
    def check_anomaly(self, user, amount):
        avg = self.get_average(user)
        if avg and amount > 5 * avg:
            return "ANOMALY"
        return "PASS"

    def check_velocity(self, user, window_minutes=5, threshold=4, amount_threshold=5000):
        history = self.user_history.get(user, [])
        if not history:
            return "PASS"

        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_transactions = [
            entry for entry in history if entry["timestamp"] >= cutoff
        ]

        total_recent_amount = sum(entry["amount"] for entry in recent_transactions)
        if len(recent_transactions) >= threshold:
            return "HIGH_RISK"
        if len(recent_transactions) >= 3 and total_recent_amount >= amount_threshold:
            return "HIGH_RISK"
        return "PASS"
