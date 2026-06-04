class GraphEngine:
    def __init__(self):
        self.graph = {}  # sender: set of receivers
    
    def add_transaction(self, sender, receiver):
        if sender not in self.graph:
            self.graph[sender] = set()
        self.graph[sender].add(receiver)
    
    def check_risk(self, sender):
        if sender in self.graph and len(self.graph[sender]) > 5:
            return "HIGH_RISK"
        return "LOW_RISK"