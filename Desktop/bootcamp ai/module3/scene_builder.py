def create_scene(material: str = "316L"):
    _mat_label = {
        "316L": "STEEL_316L", "316": "STEEL_316",
        "1.4408": "STEEL_1_4408", "1.4462": "STEEL_DUPLEX",
        "304": "STEEL_304", "carbon_steel": "CARBON_STEEL",
        "cast_iron": "CAST_IRON",
    }
    scene = {
        "camera":     "AUTO_CAMERA",
        "light":      "STUDIO_LIGHT",
        "material":   _mat_label.get(material, f"STEEL_{material}"),
        "background": "INDUSTRIAL",
    }
    return scene