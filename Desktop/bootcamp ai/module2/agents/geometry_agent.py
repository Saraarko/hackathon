def build_geometry(state):
    state["geometry"] = {
        "radius": state["diameter"] / 2,
        "length": state.get("length", 200),
        "thickness": state["thickness"],
        "flange": state["flange"]
    }

    return state