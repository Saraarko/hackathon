import json
import os
from graph import build_graph

def load_m1_data():
    """
    Loads output from Agent 1 and wraps it into state['specs'] as per the new contract.
    """
    json_path = r"e:\Documents\MY PROJECT AI\projet bootcamp\code_githhub_to_try\module1\module_1\outputs\for_module2_20260413T172657Z.json"
    
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Inject defaults if missing in Agent 1 output
        if "pressure" not in data:
            data["pressure"] = 40
        if "material" not in data:
            data["material"] = "316L"
            
        return {
            "specs": data
        }
    
    # Fallback to dummy structured data
    return {
        "specs": {
            "equipment_category": "valve",
            "dimensions": {
                "nominal_diameter_mm": 100,
                "overall_length_mm": 250
            },
            "pressure": 40,
            "material": "316L"
        }
    }

if __name__ == "__main__":
    graph = build_graph()

    # Load data from Module 1 into the specified 'specs' key
    state = load_m1_data()
    
    # Display initial extraction source
    print(f"--- Module 2 | Source: Agent 1 JSON ---")
    print(f"--- Module 2 | Running with Specs: {state['specs'].get('equipment_category')} ---")

    result = graph.invoke(state)

    print("\n--- Module 2 | Execution Done ---")
    
    # Clean result for concise display
    display_result = result.copy()
    # Remove nested specs for cleaner result printing
    if "specs" in display_result: del display_result["specs"]
    
    # Basename for paths
    for key in ["dxf", "obj", "png", "step"]:
        if key in display_result and display_result[key]:
            display_result[key] = os.path.basename(display_result[key])
    
    print(json.dumps(display_result, indent=2, default=str))