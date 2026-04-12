# services/cache_service.py

CACHE = {}

def get(key):
    return CACHE.get(key)

def set(key, value):
    CACHE[key] = value