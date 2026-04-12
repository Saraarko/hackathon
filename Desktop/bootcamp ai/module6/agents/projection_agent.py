# agents/projection_agent.py

def project(cost, inflation, years=10):
    results = []
    total = 0

    for y in range(1, years+1):
        value = cost * ((1 + inflation) ** y)
        results.append(value)
        total += value

    return total, results