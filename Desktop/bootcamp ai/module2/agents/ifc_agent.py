import os

def generate_ifc(state):
    os.makedirs("outputs", exist_ok=True)

    geo = state["geometry"]

    with open("outputs/valve.ifc", "w") as f:
        f.write(f"""
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Simple IFC'),'2;1');
ENDSEC;

DATA;
# INDUSTRIAL VALVE IFC
# Radius: {geo['radius']}
# Length: {geo['length']}
# Thickness: {geo['thickness']}
# Flange: {geo['flange']}
ENDSEC;

END-ISO-10303-21;
""")

    state["ifc"] = "outputs/valve.ifc"
    return state