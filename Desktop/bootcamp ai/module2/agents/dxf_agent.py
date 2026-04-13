import ezdxf
import os

def generate_dxf(state):
    os.makedirs("outputs", exist_ok=True)

    geo = state["geometry"]
    r = geo["radius"]

    doc = ezdxf.new()
    msp = doc.modelspace()

    # simple 2D view
    msp.add_circle((0, 0), r)
    msp.add_line((-r, 0), (r, 0))

    doc.saveas("outputs/valve.dxf")

    state["dxf"] = "outputs/valve.dxf"
    return state