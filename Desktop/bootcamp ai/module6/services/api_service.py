# services/api_service.py

import aiohttp
import asyncio
from services.cache_service import get, set

async def fetch_json(url):
    cached = get(url)
    if cached:
        return cached

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                set(url, data)
                return data
    except aiohttp.client_exceptions.ClientConnectorError:
        print(f"⚠️ Network error while fetching {url}. Using fallback mock data.")
        # Return a structure that data_agent.py correctly unpacks: [{}, [{"value": 5.0}]]
        return [{}, [{"value": 5.0}]]


async def get_all_data():
    urls = [
        "https://api.worldbank.org/v2/country/DZ/indicator/FP.CPI.TOTL.ZG?format=json",
        "https://api.open-meteo.com/v1/forecast?latitude=36&longitude=2&hourly=temperature_2m"
    ]

    results = await asyncio.gather(*(fetch_json(u) for u in urls))
    return results