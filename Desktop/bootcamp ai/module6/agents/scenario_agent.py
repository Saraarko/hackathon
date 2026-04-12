# agents/scenario_agent.py

def generate_scenarios(base_cost):
    return {
        "optimistic": base_cost * 0.9,
        "realistic": base_cost,
        "pessimistic": base_cost * 1.2
    }