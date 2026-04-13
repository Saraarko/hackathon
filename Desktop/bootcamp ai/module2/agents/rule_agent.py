def apply_design_rules(state):
    diameter = state["diameter"]
    pressure = state["pressure"]

    # 🔥 Auto Design Rules (simple mais puissant)
    thickness = 5

    if pressure > 30:
        thickness += 3

    if diameter > 80:
        thickness += 2

    flange = diameter * 1.5

    state["thickness"] = thickness
    state["flange"] = flange

    return state