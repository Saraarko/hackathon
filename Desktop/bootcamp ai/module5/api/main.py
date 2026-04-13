"""
Module 5 — ARIA Négociation IA · OpenIndustry Algérie

Flow :
  1. Démarrage → email envoyé automatiquement à chaque fournisseur
  2. Lien dans l'email : /call/S001  (token fixe = ID fournisseur, ne change jamais)
  3. Clic → appel vocal temps réel avec ARIA (Gemini)
"""

import csv, json, os, sys, uuid, smtplib, re
from contextlib import asynccontextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

import google.genai as genai
from google.genai import types as gt

_gemini       = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates     = Jinja2Templates(directory=TEMPLATES_DIR)
CSV_PATH      = os.path.join(os.path.dirname(os.path.dirname(__file__)), "suppliers.csv")

ORDER = {
    "product":           "vannes industrielles haute pression — acier inoxydable 316L",
    "quantity":          200,
    "target_price":      720.0,
    "max_price":         980.0,
    "max_delivery_days": 60,
}

# conversations actives : supplier_id → { history, status, rounds, best_price, agreement }
# La clé = supplier_id (S001, S002...) — stable, ne change pas au redémarrage
conversations: dict[str, dict] = {}


# ─── Utilitaires CSV ──────────────────────────────────────────────────────────
def load_suppliers() -> list[dict]:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def get_supplier(sid: str) -> dict | None:
    return next((s for s in load_suppliers() if s["id"] == sid), None)

def get_or_create_room(supplier_id: str) -> dict | None:
    """Retourne la salle existante ou en crée une nouvelle."""
    supplier = get_supplier(supplier_id)
    if not supplier:
        return None
    if supplier_id not in conversations:
        conversations[supplier_id] = {
            "supplier":   supplier,
            "history":    [],
            "status":     "waiting",
            "rounds":     0,
            "best_price": float(supplier["price_per_unit_usd"]),
            "agreement":  None,
        }
    return conversations[supplier_id]


# ─── Startup : envoi automatique des emails ──────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    port     = int(os.getenv("API_PORT", 8012))
    base_url = f"http://localhost:{port}"
    suppliers = load_suppliers()

    print(f"\n{'='*55}")
    print("  ARIA — Envoi automatique des invitations")
    print(f"{'='*55}")

    for s in suppliers:
        # Lien fixe basé sur l'ID — survivra aux redémarrages
        call_url   = f"{base_url}/call/{s['id']}"
        email_sent = _send_email(s["email"], s["name"], call_url, s)
        status     = "✓ Email envoyé" if email_sent else f"Lien : {call_url}"
        print(f"  {s['name']:30s} → {status}")

    print(f"{'='*55}\n")
    yield


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="ARIA — Négociation IA", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


# ─── Dashboard ────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request":   request,
        "suppliers": load_suppliers(),
        "order":     ORDER,
    })


# ─── Page d'appel (token = supplier_id, toujours valide) ─────────────────────
@app.get("/call/{supplier_id}", response_class=HTMLResponse)
async def call_page(supplier_id: str, request: Request):
    room = get_or_create_room(supplier_id)
    if not room:
        return HTMLResponse(
            "<div style='font-family:sans-serif;padding:60px;text-align:center;"
            "background:#080c10;color:#e6edf3;height:100vh;display:flex;"
            "flex-direction:column;align-items:center;justify-content:center;gap:16px'>"
            "<h2 style='color:#da3633'>Fournisseur introuvable</h2>"
            "<p style='color:#8b949e'>L'identifiant dans le lien est invalide.</p>"
            "</div>", status_code=404)

    # Reset conversation si déjà terminée
    if room["status"] in ("agreed", "rejected", "disconnected"):
        room["history"]    = []
        room["status"]     = "waiting"
        room["rounds"]     = 0
        room["best_price"] = float(room["supplier"]["price_per_unit_usd"])
        room["agreement"]  = None

    return templates.TemplateResponse("call.html", {
        "request":     request,
        "supplier_id": supplier_id,
        "supplier":    room["supplier"],
        "order":       ORDER,
    })


# ─── WebSocket vocal (clé = supplier_id) ─────────────────────────────────────
@app.websocket("/ws/call/{supplier_id}")
async def call_ws(websocket: WebSocket, supplier_id: str):
    room = get_or_create_room(supplier_id)
    if not room:
        await websocket.close(code=4004)
        return

    await websocket.accept()
    room["status"] = "connected"

    # ARIA ouvre l'appel
    opening = await _gemini_turn(supplier_id,
        f"Commence l'appel. Présente-toi à {room['supplier']['name']} et lance la négociation.")
    await websocket.send_json(opening)

    try:
        while True:
            raw  = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if data.get("type") == "speech":
                text = data.get("text", "").strip()
                if not text:
                    continue
                reply = await _gemini_turn(supplier_id, text)
                await websocket.send_json(reply)
                if reply.get("status") == "agreed":
                    await websocket.send_json({
                        "type":      "agreement",
                        "agreement": room["agreement"],
                    })
    except WebSocketDisconnect:
        room["status"] = "disconnected"


# ─── Gemini — un tour de négociation ─────────────────────────────────────────
async def _gemini_turn(supplier_id: str, user_text: str) -> dict:
    room     = conversations[supplier_id]
    supplier = room["supplier"]
    history  = room["history"]

    system = f"""Tu es ARIA, agente de négociation IA pour OpenIndustry Algérie.
Tu es en appel téléphonique avec {supplier['name']}, un fournisseur potentiel.
Tu négocies l'achat de {ORDER['quantity']} vannes industrielles haute pression acier inoxydable 316L.

FOURNISSEUR :
  Nom       : {supplier['name']} ({supplier['country']}, {supplier['city']})
  Prix cata.: {supplier['price_per_unit_usd']} USD/unité
  Délai     : {supplier['delivery_days']} jours
  Certifs.  : {supplier['certifications']}

OBJECTIFS :
  Prix cible  : {ORDER['target_price']} USD/unité
  Prix MAX    : {ORDER['max_price']} USD/unité
  Budget total: {ORDER['quantity'] * ORDER['max_price']:,.0f} USD max
  Délai max   : {ORDER['max_delivery_days']} jours

ÉTAT : Tour {room['rounds'] + 1}/8 · Meilleure offre : {room['best_price']:.2f} USD/unité

STYLE : phrases courtes et naturelles, comme au téléphone. Professionnel et tactique.
Si le fournisseur propose ≤ {ORDER['max_price']} USD → accepter et termine ta réponse par [ACCORD: X USD].
Si la négociation échoue après plusieurs refus → termine ta réponse par [REJET].
Sinon, ne mets AUCUNE balise spéciale.
Réponds en français uniquement."""

    history.append({"role": "user", "parts": [{"text": user_text}]})

    try:
        resp = _gemini.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=history,
            config=gt.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=300,
                temperature=0.8,
            ),
        )
        ai_text = resp.text or ""
    except Exception as e:
        return {"type": "error", "message": str(e)}

    history.append({"role": "model", "parts": [{"text": ai_text}]})
    room["rounds"] += 1

    status = room["status"]

    # Détection uniquement via balises explicites — évite les faux positifs
    if "[ACCORD:" in ai_text:
        m = re.search(r'\[ACCORD:\s*(\d{3,4}(?:[.,]\d{1,2})?)\s*USD\]', ai_text, re.I)
        if m:
            price = float(m.group(1).replace(",", "."))
            if price <= ORDER["max_price"]:
                status             = "agreed"
                room["status"]     = "agreed"
                room["best_price"] = price
                room["agreement"]  = {
                    "price_per_unit":     price,
                    "total_price":        round(price * ORDER["quantity"], 2),
                    "quantity":           ORDER["quantity"],
                    "supplier_name":      supplier["name"],
                    "supplier_email":     supplier["email"],
                    "delivery_days":      int(supplier["delivery_days"]),
                    "certifications":     supplier["certifications"],
                    "savings_vs_catalog": round(
                        (float(supplier["price_per_unit_usd"]) - price) * ORDER["quantity"], 2),
                }
        # Nettoyer la balise du texte affiché
        ai_text = re.sub(r'\[ACCORD:[^\]]+\]', '', ai_text).strip()

    elif "[REJET]" in ai_text:
        status         = "rejected"
        room["status"] = "rejected"
        ai_text        = ai_text.replace("[REJET]", "").strip()

    return {
        "type":   "aria",
        "text":   ai_text,          # texte déjà nettoyé des balises
        "status": status,
        "rounds": room["rounds"],
        "price":  room["best_price"],
    }


# ─── Email ────────────────────────────────────────────────────────────────────
def _send_email(to_email: str, to_name: str, call_url: str, supplier: dict) -> bool:
    sender   = os.getenv("EMAIL_SENDER", "").strip()
    password = os.getenv("EMAIL_APP_PASSWORD", "").strip()

    if not sender or not password:
        print(f"  (Email non configuré — lien : {call_url})")
        return False

    html = f"""
<div style="font-family:sans-serif;max-width:600px;margin:auto;background:#0d1117;color:#e6edf3;border-radius:12px;overflow:hidden;">
  <div style="background:linear-gradient(135deg,#1a3a5c,#0d2318);padding:32px 40px;">
    <div style="font-size:24px;font-weight:700;color:#fff;">ARIA</div>
    <div style="color:#8b949e;font-size:13px;margin-top:4px;">Agent de Négociation IA · OpenIndustry Algérie</div>
  </div>
  <div style="padding:32px 40px;">
    <p style="font-size:16px;margin-bottom:16px;">Bonjour <strong>{to_name}</strong>,</p>
    <p style="color:#8b949e;line-height:1.8;margin-bottom:24px;">
      L'équipe d'approvisionnement d'<strong style="color:#e6edf3;">OpenIndustry Algérie</strong>
      souhaite négocier avec vous une commande de
      <strong style="color:#e6edf3;">{ORDER['quantity']} vannes industrielles haute pression</strong>
      en acier inoxydable 316L.
    </p>
    <div style="background:#161b22;border:1px solid #30363d;border-radius:10px;padding:20px;margin-bottom:28px;">
      <table style="width:100%;font-size:13px;border-collapse:collapse;">
        <tr><td style="color:#8b949e;padding:5px 0;width:50%">Produit</td><td style="font-weight:700;">Vannes HP Inox 316L</td></tr>
        <tr><td style="color:#8b949e;padding:5px 0;">Quantité</td><td style="font-weight:700;">{ORDER['quantity']} unités</td></tr>
        <tr><td style="color:#8b949e;padding:5px 0;">Votre prix catalogue</td><td style="font-weight:700;">{supplier['price_per_unit_usd']} USD/u</td></tr>
        <tr><td style="color:#8b949e;padding:5px 0;">Délai souhaité</td><td style="font-weight:700;">{ORDER['max_delivery_days']} jours max</td></tr>
      </table>
    </div>
    <div style="text-align:center;margin:32px 0;">
      <a href="{call_url}" style="background:linear-gradient(135deg,#1a8cd8,#26a641);color:#fff;
         padding:18px 44px;border-radius:50px;text-decoration:none;font-size:16px;font-weight:700;
         display:inline-block;">
        🎙️ Rejoindre l'appel de négociation
      </a>
    </div>
    <p style="color:#8b949e;font-size:12px;text-align:center;line-height:1.8;">
      Durée estimée : 5–10 min · Français · Appel vocal temps réel<br/>
      Géré par <strong style="color:#4da6ff;">ARIA</strong>, l'agent IA d'OpenIndustry Algérie
    </p>
  </div>
  <div style="background:#161b22;padding:16px 40px;text-align:center;font-size:11px;color:#8b949e;border-top:1px solid #30363d;">
    OpenIndustry Algérie — Initiative citoyenne Industrie 4.0
  </div>
</div>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🎙️ ARIA vous invite — Négociation {ORDER['quantity']} vannes HP"
        msg["From"]    = f"ARIA — OpenIndustry Algérie <{sender}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"  [EMAIL ERROR] {e}")
        return False


# ─── Démarrage ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8012))
    print(f"\n{'='*55}")
    print("  ARIA — Agent de Négociation IA")
    print("  OpenIndustry Algérie — Module 5")
    print(f"{'='*55}")
    print(f"\n  ➜  http://localhost:{port}\n")
    print(f"{'='*55}\n")

    # reload=False — évite que les tokens soient recréés en boucle
    uvicorn.run("main:app", host=host, port=port, reload=False)
