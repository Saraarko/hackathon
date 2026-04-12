# agents/data_agent.py

import asyncio
from services.api_service import get_all_data

def run_data_agent(state):
    data = asyncio.run(get_all_data())

    inflation_data = data[0][1][0]['value']
    # If the API returns None (which happens for the current year), we use 0.05 (5%) as default or search the next one.
    # We will just fall back to a default of 0.05 if it's None.
    inflation = (inflation_data / 100) if inflation_data is not None else 0.05
    weather = data[1]

    state["inflation"] = inflation
    state["weather"] = weather

    return state