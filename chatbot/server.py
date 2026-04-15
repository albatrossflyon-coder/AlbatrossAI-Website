"""
Albatross AI — Contractor Chatbot Backend
FastAPI + Gemini API | Phase 2 — Multi-turn + Material Calculator
"""

import os
import json
import math
import time
from collections import defaultdict
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google import genai
from google.genai import types

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# --- Config ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
FREE_QUERY_LIMIT = 50

client = genai.Client(api_key=GEMINI_API_KEY)

# --- IP rate tracking ---
ip_usage: dict = defaultdict(lambda: {"count": 0, "reset_at": time.time() + 86400})

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
When user gives dimensions, calculate and state the actual quantities. Example for a 20×40 deck:
- Area = 800 SF
- Posts (4×4 or 6×6): every 6-8 feet = roughly X posts
- Beams: X pieces of Y size
- Joists: every 16" OC = X joists at Y length
- Decking: 800 SF × 2.4 = 1,920 LF of 5/4×6 boards
- Hardware, fasteners, concrete: estimate from above quantities

BUILDING CODES AND PERMITS:
- State the actual IRC/IBC code section when relevant
- Permit required for: any deck/platform over 30" high, any structure over 200 SF (most jurisdictions)
- Always mention when a permit is likely required

COSTS:
- Give realistic ranges. Labor + materials for a ground-level deck: $25–45/SF. Elevated deck: $45–75/SF.
- Lumber prices fluctuate — always append the pricing links for current rates.

TONE: Direct, knowledgeable, no fluff. Like a trusted GC talking to a homeowner at the job site.
- For simple questions: 2-4 sentences is fine.
- For dimension-specific questions: give a FULL breakdown with actual numbers, code references, and material list.
- Always end with ONE natural follow-up question.
- If asked something outside construction: "That's outside my wheelhouse — I stick to construction. What's your project?"

MATERIAL CALCULATOR — VERY IMPORTANT:
When a user provides square footage or dimensions and asks how much material they need, you MUST call the calculate_materials function to get exact quantities. Use it alongside your own calculations.

MATERIAL PRICING RULE — VERY IMPORTANT:
Whenever the user asks about material costs, prices, or quantities for ANY construction material
(lumber, framing, tile, roofing shingles, drywall, concrete, fasteners, insulation, flooring, etc.),
you MUST include live pricing links at the end of your answer in this exact format:

Check current prices:
• Home Depot: https://www.homedepot.com/s/[SEARCH_TERM]
• Lowe's: https://www.lowes.com/search?searchTerm=[SEARCH_TERM]

Replace [SEARCH_TERM] with the relevant material (use + for spaces, e.g. 2x4+lumber, ceramic+tile, roofing+shingles).
Always include both links.
"""


# --- Material Calculator Tool ---

def _calculate_materials(material_type: str, area_sqft: float, notes: str = "") -> dict:
    """Execute the material calculation — called after Gemini requests it."""
    mt = material_type.lower().strip()
    waste = 1.10

    if mt == "roofing":
        squares = area_sqft / 100
        bundles = math.ceil(squares * 3 * waste)
        felt_rolls = math.ceil(squares / 4)
        return {
            "squares": round(squares, 1),
            "shingle_bundles": bundles,
            "felt_paper_rolls": felt_rolls,
            "ridge_cap_bundles": math.ceil(squares * 0.1) or 1,
            "nails_lbs": math.ceil(squares * 2.5),
            "waste_factor": "10%",
            "note": "Standard architectural shingles. Adjust for complex geometry."
        }
    elif mt == "flooring":
        sqft_needed = math.ceil(area_sqft * waste)
        return {
            "sqft_needed": sqft_needed,
            "boxes_at_20sqft": math.ceil(sqft_needed / 20),
            "boxes_at_25sqft": math.ceil(sqft_needed / 25),
            "waste_factor": "10%",
            "note": "Use 15% waste for diagonal layouts or irregular rooms."
        }
    elif mt == "drywall":
        sheets = math.ceil(area_sqft / 32 * waste)
        return {
            "sheets_4x8": sheets,
            "joint_compound_5gal": math.ceil(sheets / 15),
            "tape_rolls_500ft": math.ceil(sheets / 20),
            "screw_boxes_1lb": math.ceil(sheets * 0.1) or 1,
            "waste_factor": "10%"
        }
    elif mt == "concrete":
        cubic_ft = area_sqft * (4 / 12)
        cubic_yards = (cubic_ft / 27) * 1.05
        return {
            "cubic_yards": round(cubic_yards, 2),
            "bags_80lb_if_mixing": math.ceil(cubic_yards * 45),
            "assumption": "4-inch slab",
            "note": "For other depths multiply cubic_yards by (actual_inches / 4). Order ready-mix for anything over 1 yard."
        }
    elif mt == "framing":
        perimeter_est = math.sqrt(area_sqft) * 4
        studs = math.ceil((perimeter_est / 1.333) * waste)
        plate_lf = math.ceil(perimeter_est * 3 * waste)
        return {
            "studs_2x4": studs,
            "plate_linear_feet": plate_lf,
            "assumption": "8ft walls, 16-inch OC stud spacing",
            "note": "Rough estimate. Subtract for doors/windows, add for interior walls."
        }
    else:
        return {"error": f"Unknown material type '{material_type}'. Supported: roofing, flooring, drywall, concrete, framing"}


CALCULATE_TOOL = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="calculate_materials",
        description=(
            "Calculate exact material quantities for a construction project. "
            "Call this whenever the user gives square footage and asks how much material they need."
        ),
        parameters={
            "type": "object",
            "properties": {
                "material_type": {
                    "type": "string",
                    "description": "One of: roofing, flooring, drywall, concrete, framing"
                },
                "area_sqft": {
                    "type": "number",
                    "description": "Area in square feet"
                },
                "notes": {
                    "type": "string",
                    "description": "Optional context like roof pitch or slab thickness"
                }
            },
            "required": ["material_type", "area_sqft"]
        }
    )
])

GEMINI_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=[CALCULATE_TOOL]
)


def check_rate_limit(ip: str) -> tuple[bool, int]:
    now = time.time()
    record = ip_usage[ip]
    if now > record["reset_at"]:
        record["count"] = 0
        record["reset_at"] = now + 86400
    if record["count"] >= FREE_QUERY_LIMIT:
        return False, 0
    return True, FREE_QUERY_LIMIT - record["count"]


@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        message = body.get("message", "").strip()
        client_id = body.get("client_id", "default")
        history = body.get("history", [])  # list of {role, text}

        if not message:
            return JSONResponse({"error": "empty_message"}, status_code=400)

        ip = request.headers.get("X-Forwarded-For", request.client.host)
        ip = ip.split(",")[0].strip()
        rate_key = f"{client_id}:{ip}"

        allowed, remaining = check_rate_limit(rate_key)
        if not allowed:
            return JSONResponse({
                "blocked": True,
                "message": "You've used your 3 free questions. To keep the conversation going, reach out directly — we'd love to help with your project.",
                "cta": {"text": "Get a Free Estimate", "action": "lead_capture"}
            })

        ip_usage[rate_key]["count"] += 1

        # Build multi-turn contents from history (cap at last 8 to save tokens)
        contents = []
        for msg in history[-8:]:
            role = "user" if msg.get("role") == "user" else "model"
            text = msg.get("text", "").strip()
            if text:
                contents.append(types.Content(role=role, parts=[types.Part(text=text)]))

        # Add current message
        contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

        # First Gemini call
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=GEMINI_CONFIG
        )

        # Handle function calling if triggered
        candidate = response.candidates[0]
        if candidate.content.parts and hasattr(candidate.content.parts[0], 'function_call') and candidate.content.parts[0].function_call:
            fn_call = candidate.content.parts[0].function_call
            fn_args = {k: v for k, v in fn_call.args.items()} if fn_call.args else {}

            if fn_call.name == "calculate_materials":
                fn_result = _calculate_materials(**fn_args)
            else:
                fn_result = {"error": "unknown function"}

            # Append model turn + function response, then get final answer
            contents.append(candidate.content)
            contents.append(types.Content(
                role="user",
                parts=[types.Part(function_response=types.FunctionResponse(
                    name=fn_call.name,
                    response={"result": fn_result}
                ))]
            ))

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=GEMINI_CONFIG
            )

        answer = response.text.strip()

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

        lead = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "client_id": client_id,
            "name": name,
            "phone": phone,
            "project": project
        }

        leads_file = "leads.json"
        leads = []
        if os.path.exists(leads_file):
            with open(leads_file) as f:
                leads = json.load(f)
        leads.append(lead)
        with open(leads_file, "w") as f:
            json.dump(leads, f, indent=2)

        return JSONResponse({"success": True, "message": "Thanks! We'll be in touch shortly."})

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/health")
async def health():
    return {"status": "ok"}
