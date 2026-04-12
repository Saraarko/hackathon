# agents/montecarlo_agent.py

import random

def run_montecarlo(base, inflation, runs=800):
    res = []

    for _ in range(runs):
        inf = inflation + random.uniform(-0.01, 0.02)
        cost = base * (1 + inf)
        res.append(cost)

    return {
        "mean": sum(res)/len(res),
        "min": min(res),
        "max": max(res)
    }