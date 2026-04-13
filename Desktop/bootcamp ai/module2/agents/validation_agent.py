def validate(state):
    geo = state["geometry"]

    warnings = []

    if geo["radius"] <= 0:
        raise ValueError("Invalid radius")

    if geo["thickness"] < 3:
        warnings.append("Wall too thin")

    if geo["flange"] < geo["radius"] * 1.2:
        warnings.append("Flange ratio low")

    state["validation"] = {
        "status": "OK",
        "warnings": warnings
    }

    return state