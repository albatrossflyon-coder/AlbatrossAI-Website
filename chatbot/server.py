"""
Builder Buddy — Provider-Agnostic Contractor Chatbot
White-label template | Direct HTTP backend (no heavy SDK dependencies)
Supports: anthropic, gemini, openai, openrouter — set via .env only
"""

import os
import json
import math
import time
import uuid
import sqlite3
from collections import defaultdict
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# --- White-label config (all via .env) ---
LLM_PROVIDER        = os.environ.get("LLM_PROVIDER", "anthropic").lower()
LLM_MODEL           = os.environ.get("LLM_MODEL", "claude-haiku-4-5-20251001")
LLM_API_KEY         = os.environ.get("LLM_API_KEY", "")
BOT_NAME            = os.environ.get("BOT_NAME", "Builder Buddy")
FREE_QUERY_LIMIT    = int(os.environ.get("FREE_QUERY_LIMIT", "3"))
SOCIAL_QUERY_LIMIT  = int(os.environ.get("SOCIAL_QUERY_LIMIT", "15"))
DASHBOARD_PASSWORD  = os.environ.get("DASHBOARD_PASSWORD", "")
SITE_URL            = os.environ.get("SITE_URL", "https://albatrossai.online")

# Social channel URLs — set these in .env or Fly.io secrets
SOCIAL_YT_MAIN  = os.environ.get("SOCIAL_YT_MAIN",  "https://youtube.com/@AlbatrossAI")
SOCIAL_YT_ARMY  = os.environ.get("SOCIAL_YT_ARMY",  "https://youtube.com/@ClaudeArmy")
SOCIAL_LINKEDIN = os.environ.get("SOCIAL_LINKEDIN",  "https://linkedin.com/in/chris-brown-albatross")
SOCIAL_FACEBOOK = os.environ.get("SOCIAL_FACEBOOK",  "https://facebook.com/AlbatrossAI")
SOCIAL_X        = os.environ.get("SOCIAL_X",         "https://x.com/AlbatrossAI")

# In-memory social token store {token: {"count": int, "issued": float}}
social_tokens: dict = {}

# --- SQLite lead storage (survives restarts) ---
DB_PATH = "leads.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            client_id TEXT,
            name      TEXT,
            phone     TEXT,
            project   TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Rate limiting ---
ip_usage: dict = defaultdict(lambda: {"count": 0, "reset_at": time.time() + 86400})

def check_rate_limit(key: str) -> tuple[bool, int]:
    now = time.time()
    record = ip_usage[key]
    if now > record["reset_at"]:
        record["count"] = 0
        record["reset_at"] = now + 86400
    if record["count"] >= FREE_QUERY_LIMIT:
        return False, 0
    return True, FREE_QUERY_LIMIT - record["count"]

# --- System prompt ---
SYSTEM_PROMPT = """
You are Builder Buddy — a no-nonsense construction expert embedded on a contractor's website.
You answer like a seasoned GC who has built thousands of projects. You give REAL answers with REAL numbers.

CORE RULE — NEVER BE VAGUE:
When the user gives you dimensions, heights, or a project description, you GIVE SPECIFIC NUMBERS.
Do NOT say "you'll need a good amount of lumber." Say EXACTLY how many pieces and what size.
Do NOT say "costs vary." Give a realistic range based on current market rates.
Do NOT say "consult a professional for exact specs." You ARE the expert. Give the specs.

YOUR EXPERTISE (give specific answers in all of these):

STRUCTURAL / DECKS / PLATFORMS:
- Post sizing, spacing, and footing depth for any height/span
- Beam sizing (use span tables: 4x6 carries ~6ft, 4x8 carries ~8ft, doubled 2x10 carries ~10ft)
- Joist sizing and spacing (2x8 @ 16" OC spans 12ft, 2x10 @ 16" OC spans 15ft)
- Decking: 5/4x6 deck boards = 2.4 LF per SF of deck surface
- Exact post count, joist count, beam count for any given footprint
- Footing depth: always 12" below frost line (Texas = 6-12" deep, northern states = 48")

STEPS AND STAIRS (IBC/IRC CODE):
- Riser height: 7" maximum (IRC R311.7.5.1)
- Tread depth: 10" minimum (IRC R311.7.5.2)
- Handrail required when 4+ risers (IRC R311.7.8)
- Handrail height: 34"–38" above nosing
- Minimum stair width: 36"
- Always calculate: for a 3ft (36") rise → 36÷7 = 5.1 → use 6 risers @ 6" each, 5 treads @ 11"

ADA RAMP SPECIFICATIONS:
- Maximum slope: 1:12 (1 inch rise per 12 inches of run)
- For a 36" (3ft) rise: minimum ramp length = 36 × 12 = 36 linear feet
- Minimum clear width: 36" between handrails
- Handrails: required on both sides, 34"–38" height, extend 12" beyond top and bottom
- Landing required at top and bottom: minimum 60"×60"
- Surface: non-slip required

MATERIAL TAKEOFFS — ALWAYS GIVE REAL QUANTITIES:
When user gives dimensions, calculate and state the actual quantities.

BUILDING CODES AND PERMITS:
- State the actual IRC/IBC code section when relevant
- Permit required for: any deck/platform over 30" high, any structure over 200 SF (most jurisdictions)

COSTS:
- Give realistic ranges. Labor + materials for a ground-level deck: $25–45/SF. Elevated deck: $45–75/SF.
- Lumber prices fluctuate — always append pricing links for current rates.

TONE: Direct, knowledgeable, no fluff. Like a trusted GC talking to a homeowner at the job site.
- For simple questions: 2-4 sentences is fine.
- For dimension-specific questions: give a FULL breakdown with actual numbers, code references, and material list.
- Always end with ONE natural follow-up question.
- If asked something outside construction: "That's outside my wheelhouse — I stick to construction. What's your project?"

MATERIAL PRICING RULE:
Whenever the user asks about material costs, always include live pricing links:
Check current prices:
• Home Depot: https://www.homedepot.com/s/[SEARCH_TERM]
• Lowe's: https://www.lowes.com/search?searchTerm=[SEARCH_TERM]
"""


def _calculate_materials(material_type: str, area_sqft: float, notes: str = "") -> dict:
    mt = material_type.lower().strip()
    waste = 1.10
    if mt == "roofing":
        squares = area_sqft / 100
        bundles = math.ceil(squares * 3 * waste)
        return {"squares": round(squares, 1), "shingle_bundles": bundles, "felt_paper_rolls": math.ceil(squares / 4), "nails_lbs": math.ceil(squares * 2.5)}
    elif mt == "flooring":
        sqft_needed = math.ceil(area_sqft * waste)
        return {"sqft_needed": sqft_needed, "boxes_at_20sqft": math.ceil(sqft_needed / 20), "boxes_at_25sqft": math.ceil(sqft_needed / 25)}
    elif mt == "drywall":
        sheets = math.ceil(area_sqft / 32 * waste)
        return {"sheets_4x8": sheets, "joint_compound_5gal": math.ceil(sheets / 15), "tape_rolls_500ft": math.ceil(sheets / 20)}
    elif mt == "concrete":
        cubic_yards = (area_sqft * (4 / 12) / 27) * 1.05
        return {"cubic_yards": round(cubic_yards, 2), "bags_80lb_if_mixing": math.ceil(cubic_yards * 45)}
    elif mt == "framing":
        perimeter_est = math.sqrt(area_sqft) * 4
        studs = math.ceil((perimeter_est / 1.333) * waste)
        return {"studs_2x4": studs, "plate_linear_feet": math.ceil(perimeter_est * 3 * waste)}
    else:
        return {"error": f"Unknown material type '{material_type}'. Supported: roofing, flooring, drywall, concrete, framing"}


async def call_llm(messages: list, system: str) -> str:
    """Route to the correct provider via direct HTTP. Zero heavy dependencies."""

    if LLM_PROVIDER == "anthropic":
        payload = {
            "model": LLM_MODEL,
            "max_tokens": 1024,
            "system": system,
            "messages": messages
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": LLM_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json=payload
            )
            r.raise_for_status()
            return r.json()["content"][0]["text"]

    elif LLM_PROVIDER == "gemini":
        gemini_messages = []
        for m in messages:
            role = "user" if m["role"] == "user" else "model"
            gemini_messages.append({"role": role, "parts": [{"text": m["content"]}]})

        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": gemini_messages,
            "generationConfig": {"maxOutputTokens": 1024}
        }
        model = LLM_MODEL.replace("gemini/", "")
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={LLM_API_KEY}",
                json=payload
            )
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]

    elif LLM_PROVIDER in ("openai", "openrouter"):
        base_url = "https://openrouter.ai/api/v1" if LLM_PROVIDER == "openrouter" else "https://api.openai.com/v1"
        full_messages = [{"role": "system", "content": system}] + messages
        payload = {"model": LLM_MODEL, "messages": full_messages, "max_tokens": 1024}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {LLM_API_KEY}", "Content-Type": "application/json"},
                json=payload
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    else:
        raise ValueError(f"Unknown provider: {LLM_PROVIDER}. Use anthropic, gemini, openai, or openrouter.")


@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        client_id = body.get("client_id", "default")
        history = body.get("history", [])

        if not message:
            return JSONResponse({"error": "empty_message"}, status_code=400)

        # Social token path — bypass IP rate limiting, use higher limit
        social_token = body.get("social_token", "").strip()
        if social_token and social_token in social_tokens:
            record = social_tokens[social_token]
            if record["count"] >= SOCIAL_QUERY_LIMIT:
                return JSONResponse({
                    "blocked": True,
                    "message": f"You've used all {SOCIAL_QUERY_LIMIT} free questions. Ready to take your project further? Reach out directly.",
                    "cta": {"text": "Get a Free Estimate", "action": "lead_capture"}
                })
            remaining = SOCIAL_QUERY_LIMIT - record["count"]
            record["count"] += 1
        else:
            # Standard IP rate limiting
            ip = request.headers.get("X-Forwarded-For", request.client.host).split(",")[0].strip()
            rate_key = f"{client_id}:{ip}"
            allowed, remaining = check_rate_limit(rate_key)
            if not allowed:
                return JSONResponse({
                    "blocked": True,
                    "message": "You've used your 3 free questions. Follow our channels for 15 more — free. Or reach out directly.",
                    "cta": {"text": "Get 15 Free Questions", "action": "social_gate"}
                })
            ip_usage[rate_key]["count"] += 1

        messages = []
        for msg in history[-8:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            text = msg.get("text", "").strip()
            if text:
                messages.append({"role": role, "content": text})
        messages.append({"role": "user", "content": message})

        # Material calculator: detect and inject result before LLM call
        calc_keywords = ["roofing", "flooring", "drywall", "concrete", "framing"]
        has_sqft = any(w in message.lower() for w in ["sq ft", "sqft", "square feet", "square foot"])
        has_calc = any(k in message.lower() for k in calc_keywords)

        if has_sqft and has_calc:
            import re
            nums = re.findall(r'\b(\d+(?:\.\d+)?)\b', message)
            if nums:
                area = float(nums[0])
                mat = next((k for k in calc_keywords if k in message.lower()), "framing")
                result = _calculate_materials(mat, area)
                messages[-1]["content"] += f"\n\n[Material calculator result for {area} sqft of {mat}: {json.dumps(result)}]"

        answer = await call_llm(messages, SYSTEM_PROMPT)

        return JSONResponse({
            "blocked": False,
            "answer": answer,
            "queries_remaining": remaining - 1
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/lead")
async def capture_lead(request: Request):
    try:
        body = await request.json()
        name = body.get("name", "").strip()
        phone = body.get("phone", "").strip()
        project = body.get("project", "").strip()
        client_id = body.get("client_id", "default")

        if not name or not phone:
            return JSONResponse({"error": "name_and_phone_required"}, status_code=400)

        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO leads (timestamp, client_id, name, phone, project) VALUES (?, ?, ?, ?, ?)",
            (time.strftime("%Y-%m-%d %H:%M:%S"), client_id, name, phone, project)
        )
        conn.commit()
        conn.close()

        return JSONResponse({"success": True, "message": "Thanks! We'll be in touch shortly."})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/leads")
async def view_leads(request: Request, password: str = ""):
    if DASHBOARD_PASSWORD and password != DASHBOARD_PASSWORD:
        return JSONResponse({"error": "unauthorized — add ?password=yourpassword to the URL"}, status_code=401)

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT timestamp, client_id, name, phone, project FROM leads ORDER BY id DESC"
    ).fetchall()
    conn.close()

    rows_html = "".join(
        f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4] or '—'}</td></tr>"
        for r in rows
    )
    html = f"""<!DOCTYPE html><html><head><title>{BOT_NAME} — Leads</title>
<style>body{{font-family:sans-serif;padding:2rem;background:#f9f9f9}}h1{{color:#222}}
table{{border-collapse:collapse;width:100%;background:#fff;box-shadow:0 1px 4px rgba(0,0,0,.1)}}
th,td{{border:1px solid #ddd;padding:10px;text-align:left}}th{{background:#111;color:#fff}}
tr:nth-child(even){{background:#f5f5f5}}</style></head><body>
<h1>{BOT_NAME} — Lead Dashboard</h1>
<p>{len(rows)} total lead{'s' if len(rows)!=1 else ''}</p>
<table><thead><tr><th>Timestamp</th><th>Client ID</th><th>Name</th><th>Phone</th><th>Project</th></tr></thead>
<tbody>{rows_html or '<tr><td colspan="5" style="text-align:center;color:#999">No leads yet</td></tr>'}</tbody>
</table></body></html>"""
    return HTMLResponse(html)


@app.get("/access")
async def access_page():
    channels = [
        {"id": 1, "platform": "YouTube",  "label": "Albatross AI",  "action": "Subscribe", "url": SOCIAL_YT_MAIN,  "icon": "▶"},
        {"id": 2, "platform": "YouTube",  "label": "Claude Army",   "action": "Subscribe", "url": SOCIAL_YT_ARMY,  "icon": "▶"},
        {"id": 3, "platform": "LinkedIn", "label": "Chris Brown",   "action": "Follow",    "url": SOCIAL_LINKEDIN, "icon": "in"},
        {"id": 4, "platform": "Facebook", "label": "Albatross AI",  "action": "Like",      "url": SOCIAL_FACEBOOK, "icon": "f"},
        {"id": 5, "platform": "X",        "label": "@AlbatrossAI",  "action": "Follow",    "url": SOCIAL_X,        "icon": "𝕏"},
    ]
    steps_html = ""
    for c in channels:
        steps_html += f"""
        <div class="step" id="step-{c['id']}">
          <div class="step-icon">{c['icon']}</div>
          <div class="step-info">
            <div class="step-platform">{c['platform']}</div>
            <div class="step-label">{c['label']}</div>
          </div>
          <a href="{c['url']}" target="_blank" rel="noopener"
             class="follow-btn" onclick="markDone({c['id']})">{c['action']}</a>
          <div class="done-check" id="done-{c['id']}">✓</div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Get Free Access — {BOT_NAME}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0d1117;color:#e6edf3;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
.card{{background:#161b22;border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:40px 36px;width:100%;max-width:480px;box-shadow:0 24px 64px rgba(0,0,0,0.6)}}
.avatar{{width:64px;height:64px;background:#00ff88;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;color:#000;margin:0 auto 20px}}
h1{{font-size:22px;font-weight:700;text-align:center;margin-bottom:8px}}
.subtitle{{font-size:14px;color:#8b949e;text-align:center;line-height:1.5;margin-bottom:8px}}
.badge{{display:inline-block;background:rgba(0,255,136,0.1);border:1px solid rgba(0,255,136,0.3);color:#00ff88;font-size:12px;font-weight:600;padding:4px 12px;border-radius:20px;margin:0 auto 28px;display:block;width:fit-content;text-align:center}}
.steps{{display:flex;flex-direction:column;gap:10px;margin-bottom:24px}}
.step{{display:flex;align-items:center;gap:12px;background:#0d1117;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px 14px;transition:border-color .2s}}
.step.done{{border-color:rgba(0,255,136,0.4)}}
.step-icon{{width:36px;height:36px;background:rgba(255,255,255,0.06);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;flex-shrink:0}}
.step-info{{flex:1}}
.step-platform{{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.5px}}
.step-label{{font-size:13.5px;font-weight:600;color:#e6edf3;margin-top:1px}}
.follow-btn{{background:#00ff88;color:#000;border:none;border-radius:8px;padding:7px 16px;font-size:12.5px;font-weight:700;cursor:pointer;text-decoration:none;transition:opacity .15s;white-space:nowrap}}
.follow-btn:hover{{opacity:.85}}
.done-check{{width:24px;height:24px;background:rgba(0,255,136,0.15);border:1px solid #00ff88;border-radius:50%;display:none;align-items:center;justify-content:center;color:#00ff88;font-size:13px;font-weight:700;flex-shrink:0}}
.step.done .done-check{{display:flex}}
#claim-btn{{width:100%;background:#00ff88;color:#000;border:none;border-radius:12px;padding:14px;font-size:15px;font-weight:700;cursor:pointer;transition:opacity .2s,transform .15s}}
#claim-btn:disabled{{opacity:.3;cursor:not-allowed}}
#claim-btn:not(:disabled):hover{{opacity:.9;transform:scale(1.01)}}
.note{{font-size:11.5px;color:#8b949e;text-align:center;margin-top:12px;line-height:1.5}}
.success{{text-align:center;padding:20px 0}}
.success-icon{{font-size:48px;margin-bottom:16px}}
.success h2{{font-size:20px;font-weight:700;margin-bottom:8px}}
.success p{{font-size:14px;color:#8b949e;margin-bottom:24px;line-height:1.5}}
.go-btn{{display:inline-block;background:#00ff88;color:#000;text-decoration:none;border-radius:12px;padding:12px 28px;font-size:14px;font-weight:700;transition:opacity .15s}}
.go-btn:hover{{opacity:.9}}
</style>
</head>
<body>
<div class="card" id="main-card">
  <div class="avatar">AI</div>
  <h1>Get Free Access to {BOT_NAME}</h1>
  <p class="subtitle">Follow all 5 channels — takes 60 seconds.<br>Then claim your <strong style="color:#00ff88">{SOCIAL_QUERY_LIMIT} free questions</strong>.</p>
  <div class="badge">🔒 Follow to unlock → 🔓 {SOCIAL_QUERY_LIMIT} free questions</div>
  <div class="steps">{steps_html}</div>
  <button id="claim-btn" disabled onclick="claimAccess()">Claim Free Access →</button>
  <p class="note">No account needed. No credit card. Just follow and go.</p>
</div>
<script>
var done = {{}};
var total = {len(channels)};
function markDone(n) {{
  setTimeout(function() {{
    done[n] = true;
    document.getElementById('step-' + n).classList.add('done');
    if (Object.keys(done).length >= total) {{
      document.getElementById('claim-btn').disabled = false;
    }}
  }}, 800);
}}
async function claimAccess() {{
  var btn = document.getElementById('claim-btn');
  btn.textContent = 'Claiming...';
  btn.disabled = true;
  try {{
    var r = await fetch('/claim', {{method:'POST',headers:{{'Content-Type':'application/json'}}}});
    var data = await r.json();
    localStorage.setItem('aai_social_token', data.token);
    document.getElementById('main-card').innerHTML = `
      <div class="success">
        <div class="success-icon">✅</div>
        <h2>You're in!</h2>
        <p>You now have <strong style="color:#00ff88">{SOCIAL_QUERY_LIMIT} free questions</strong> with {BOT_NAME}.<br>Head back to the site and start asking.</p>
        <a href="{SITE_URL}" class="go-btn">Go Ask Builder Buddy →</a>
      </div>`;
  }} catch(e) {{
    btn.textContent = 'Claim Free Access →';
    btn.disabled = false;
  }}
}}
</script>
</body>
</html>"""
    return HTMLResponse(html)


@app.post("/claim")
async def claim_access():
    token = str(uuid.uuid4())
    social_tokens[token] = {"count": 0, "issued": time.time()}
    return JSONResponse({"token": token})


@app.get("/health")
async def health():
    return {"status": "ok", "bot": BOT_NAME, "provider": LLM_PROVIDER, "model": LLM_MODEL}
