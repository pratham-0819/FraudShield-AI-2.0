class HeuristicEngine:
    def __init__(self):
        pass
    
    def calculate_score(self, amount, time, device, scenario):
        score = 0
        
        # Escalate very large amounts more aggressively.
        if amount >= 100000:
            score += 90
        elif amount >= 10000:
            score += 60
        elif amount > 1000:
            score += 30
        
        # Night transaction (22-6) -> +20
        hour = int(time.split(':')[0]) if ':' in time else 12
        if hour >= 22 or hour <= 6:
            score += 20
        
        # Unknown device -> +20 (assume if device == 'unknown')
        if device.lower() == 'unknown':
            score += 20
        
        # Fraud scenario -> +25-30
        if scenario.lower() in ['stolen card', 'phishing']:
            score += 25
        
        return score

    def estimate_probability(self, amount, time, device, scenario):
        probability = 0.0

        if amount >= 100000:
            probability += 0.55
        elif amount >= 10000:
            probability += 0.35
        elif amount > 1000:
            probability += 0.15

        hour = int(time.split(':')[0]) if ':' in time else 12
        if hour >= 22 or hour <= 6:
            probability += 0.15

        if device.lower() == 'unknown':
            probability += 0.20

        if scenario.lower() in ['stolen card', 'phishing']:
            probability += 0.20

        return min(probability, 0.95)
