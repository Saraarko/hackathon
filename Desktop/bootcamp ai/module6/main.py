import os
from graph import build_graph
def ensure_output_dir():
    os.makedirs("outputs", exist_ok=True)


if __name__ == "__main__":
    ensure_output_dir()

    graph = build_graph()

    state = {
        "base_cost": 50000
    }

    result = graph.invoke(state)