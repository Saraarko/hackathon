import logging
from typing import Any, Dict, Optional
from .exporters import generate_excel, generate_pdf

# Configure production logging
logger = logging.getLogger("IndustrieIA.Agent7")

def validate_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Production-grade validation of the agent state.
    Ensures upstream keys exist with technical zero/empty fallbacks 
    to prevent runtime attribute errors in a LangGraph pipeline.
    """
    required_keys = {
        "specs": {},
        "suppliers": [],
        "tco": {"total_cost_10y": 0, "maintenance": 0},
        "quantity": 0,
        "price_per_unit": 0,
        "financials": {},
        "projections": [],
        "npv": 0.0,
        "decision": "N/A",
        "swot": "",
        "summary": ""
    }
    
    for key, default_val in required_keys.items():
        if key not in state or state[key] is None:
            state[key] = default_val
        elif isinstance(default_val, dict):
            # Ensure sub-keys exist for nested structures
            for subkey, subval in default_val.items():
                if subkey not in state[key]:
                    state[key][subkey] = subval
            
    return state

def compute_financials(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates primary financial metrics (Year 1).
    Dependent on: quantity, price_per_unit, tco.
    """
    try:
        qty = state.get("quantity", 0)
        ppu = state.get("price_per_unit", 0)
        tco_10 = state.get("tco", {}).get("total_cost_10y", 0)
        
        revenue = ppu * qty
        # Annualized TCO cost (assuming 10-year project lifecycle)
        annual_cost = tco_10 / 10 if tco_10 > 0 else 0
        profit = revenue - annual_cost
        roi = profit / annual_cost if annual_cost > 0 else 0.0
        
        state["financials"] = {
            "revenue": float(revenue),
            "profit": float(profit),
            "roi": float(roi),
            "roi_str": f"{roi:.2%}"
        }
    except Exception as e:
        logger.error(f"Agent 7 - Financial calculation error: {e}")
    return state

def compute_projections_and_npv(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs 3-year growth simulation and Net Present Value (NPV) computation.
    Uses standard discount rate (10%) and revenue growth (10%).
    """
    try:
        qty = state.get("quantity", 0)
        ppu = state.get("price_per_unit", 0)
        tco_10 = state.get("tco", {}).get("total_cost_10y", 0)
        
        growth = 0.10
        discount = 0.10
        annual_cost = tco_10 / 10 
        
        projections = []
        for year in range(1, 4):
            rev = (qty * ppu) * ((1 + growth) ** (year - 1))
            prof = rev - annual_cost
            roi = prof / annual_cost if annual_cost > 0 else 0.0
            
            projections.append({
                "year": year,
                "revenue": float(rev),
                "profit": float(prof),
                "roi": float(roi),
                "roi_str": f"{roi:.2%}"
            })
            
        state["projections"] = projections
        state["total_3y_profit"] = sum(p["profit"] for p in projections)
        
        # NPV = sum(Cashflow_t / (1 + r)^t)
        npv = sum(p["profit"] / ((1 + discount) ** p["year"]) for p in projections)
        state["npv"] = float(npv)
        
    except Exception as e:
        logger.error(f"Agent 7 - Projections calculation error: {e}")
        state["projections"] = []
        state["npv"] = 0.0
        
    return state

def make_decision(state: Dict[str, Any]) -> Dict[str, Any]:
    """Investment viability screening."""
    npv = state.get("npv", 0.0)
    roi_y1 = state.get("financials", {}).get("roi", 0.0)
    
    if npv > 0 and roi_y1 > 0.1:
        decision = "STRATEGIC INVESTMENT (NPV+)"
    elif npv <= 0 and roi_y1 > 0:
        decision = "SHORT-TERM VIABLE (NPV-)"
    else:
        decision = "NOT RECOMMENDED"
        
    state["decision"] = decision
    return state

def _call_llm(llm: Any, prompt: str) -> str:
    """Interface to standardize LLM response extraction."""
    try:
        if hasattr(llm, "invoke"):
            res = llm.invoke(prompt)
            return res.content if hasattr(res, 'content') else str(res)
        elif callable(llm):
            return str(llm(prompt))
        return "LLM Interface missing."
    except Exception as e:
        logger.error(f"Agent 7 - AI call error: {e}")
        return f"AI Generation Error: {str(e)}"

def generate_swot(state: Dict[str, Any], llm: Any) -> Dict[str, Any]:
    """Orchestrates AI-driven SWOT analysis based on real state data."""
    specs_type = state.get('specs', {}).get('type', 'Industrial Project')
    npv = state.get('npv', 0.0)
    
    prompt = f"""
    Analyze the industrial investment project: {specs_type}.
    Financial viability indicators: 3-year NPV of ${npv:,.2f}.
    Perform a professional SWOT analysis (Strengths, Weaknesses, Opportunities, Threats).
    """
    state["swot"] = _call_llm(llm, prompt)
    return state

def generate_summary(state: Dict[str, Any], llm: Any) -> Dict[str, Any]:
    """Generates an executive strategy summary."""
    prompt = f"""
    Summarize the business case for this project.
    Recommendation: {state.get('decision', 'N/A')}
    KPIs: NPV of ${state.get('npv', 0.0):,.2f}, Total 3Y Profit of ${state.get('total_3y_profit', 0.0):,.2f}.
    """
    state["summary"] = _call_llm(llm, prompt)
    return state

def business_agent(state: Dict[str, Any], llm: Any) -> Dict[str, Any]:
    """
    INDUSTRIE IA: Agent 7 Node (Business Plan).
    Pure function interface for LangGraph pipeline orchestration.
    """
    logger.info("Agent 7 node activated.")
    
    # Node logic sequence
    state = validate_state(state)
    state = compute_financials(state)
    state = compute_projections_and_npv(state)
    state = make_decision(state)
    state = generate_swot(state, llm)
    state = generate_summary(state, llm)
    
    # Reporting generation
    try:
        generate_excel(state)
        generate_pdf(state)
    except Exception as e:
        logger.warning(f"Agent 7 - Reporting layer exception: {e}")
    
    logger.info("Agent 7 node completed.")
    return state
