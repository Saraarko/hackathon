# agents/report_agent.py

from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from jinja2 import Environment, FileSystemLoader
import json


# 📊 Excel
def generate_excel(state):
    wb = Workbook()

    ws = wb.active
    ws.title = "Summary"
    ws.append(["Metric", "Value"])
    ws.append(["Total Cost", state["total_cost"]])
    ws.append(["ROI", state["roi"]])
    ws.append(["Risk", state["risk"]["risk_level"]])

    wb.save("outputs/tco.xlsx")
    return state


# 🌐 HTML Dashboard
def generate_html(state):
    html = f"""
    <h1>TCO Dashboard</h1>
    <p>Total Cost: {state['total_cost']}</p>
    <p>ROI: {state['roi']}</p>
    <p>Risk: {state['risk']['risk_level']}</p>
    """

    with open("outputs/dashboard.html", "w") as f:
        f.write(html)

    return state


# 📄 PDF
def generate_pdf(state):
    doc = SimpleDocTemplate("outputs/report.pdf")
    styles = getSampleStyleSheet()

    content = [
        Paragraph("TCO Report", styles["Title"]),
        Paragraph(f"Total Cost: {state['total_cost']}", styles["Normal"]),
        Paragraph(f"ROI: {state['roi']}", styles["Normal"]),
        Paragraph(f"Risk: {state['risk']['risk_level']}", styles["Normal"]),
    ]

    doc.build(content)
    return state


# 🔗 JSON
def generate_json(state):
    with open("outputs/tco.json", "w") as f:
        json.dump(state, f, indent=2)

    return state


# 🎯 MASTER FUNCTION
def generate_all_outputs(state):
    state = generate_excel(state)
    state = generate_html(state)
    state = generate_pdf(state)
    state = generate_json(state)

    return state