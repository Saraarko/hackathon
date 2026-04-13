from graph import build_graph

if __name__ == "__main__":
    graph = build_graph()

    # INPUT venant du Module 1 (simulé ici)
    state = {
        "type": "valve",
        "diameter": 100,
        "pressure": 40,
        "material": "316L",
        "length": 250
    }

    result = graph.invoke(state)

    print("MODULE 2 DONE")
    print(result)