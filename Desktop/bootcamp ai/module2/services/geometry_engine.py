# services/geometry_engine.py

def build_geometry(specs):
    return {
        "radius": specs["diameter"] / 2,
        "length": 200,
        "thickness": specs["thickness"],
        "flange": specs["flange"]
    }