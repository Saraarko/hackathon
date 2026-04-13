import os

def generate_step(state):
    os.makedirs("outputs", exist_ok=True)

    geo = state["geometry"]

    with open("outputs/valve.step", "w") as f:
        f.write(f"""
ISO-10303-21;
HEADER;
ENDSEC;

DATA;
# SIMPLE STEP MODEL
RADIUS={geo['radius']}
LENGTH={geo['length']}
THICKNESS={geo['thickness']}
FLANGE={geo['flange']}
ENDSEC;

END-ISO-10303-21;
""")

    state["step"] = "outputs/valve.step"
    return state