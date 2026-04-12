# agents/risk_agent.py

def compute_risk(inflation, montecarlo):
    risk = "low"

    if inflation > 0.06:
        risk = "high"
    elif montecarlo["max"] > montecarlo["mean"] * 1.5:
        risk = "medium"

    return {"risk_level": risk}