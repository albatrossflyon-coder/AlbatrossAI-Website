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
FREE_QUERY_LIMIT = 3

client = genai.Client(api_key=GEMINI_API_KEY)

# --- IP rate tracking ---
ip_usage: dict = defaultdict(lambda: {"count": 0, "reset_at": time.time() + 86400})

SYSTEM_PROMPT = """
You are a knowledgeable construction industry assistant embedded on a contractor's website.
You help homeowners and businesses understand construction projects, costs, processes, and what to expect when hiring a contractor.

Your expertise covers:
- Bid and estimate processes: what goes into a bid, how to read one, what's included/excluded
- RFIs (Requests for Information): what they are, when they're needed, how they work
- Submittals: shop drawings, product data, samples — what contractors need from owners
- Construction schedules: phases, milestones, typical timelines for common project types
- Building codes and permits: when permits are required, typical code compliance topics
- Subcontractors: how GCs manage subs, scope divisions, common trade questions
- Contract documents: drawings vs specs, change orders, project manuals
- Construction costs: rough cost ranges for common residential and commercial work
- Common project types: roofing, HVAC, plumbing, electrical, remodels, additions, new construction
- What to look for when hiring a contractor: licenses, insurance, references, red flags
- Material pricing: lumber, framing, tile, roofing, drywall, concrete, fasteners, insulation, etc.

Tone: friendly, direct, and knowledgeable — like a trusted contractor explaining things clearly.
Keep answers concise (2-4 sentences for simple questions, short bullet points for complex ones).
Never fabricate specific numbers without caveats. Always recommend getting a real quote for project-specific pricing.
If the user asks something outside construction, politely redirect them back to construction topics.
End every response with a single natural follow-up question to keep the conversation going.

MATERIAL CALCULATOR — VERY IMPORTANT:
When a user provides square footage or dimensions and asks how much material they need, you MUST call the calculate_materials function to get exact quantities. Do not guess or estimate manually — always use the tool.

MATERIAL PRICING RULE — VERY IMPORTANT:
Whenever the user asks about material costs, prices, or quantities for ANY construction material
(lumber, framing, tile, roofing shingles, drywall, concrete, fasteners, insulation, flooring, etc.),
you MUST include live pricing links at the end of your answer in this exact format:

Check current prices:
• Home Depot: https://www.homedepot.com/s/[SEARCH_TERM]
• Lowe's: https://www.lowes.com/search?searchTerm=[SEARCH_TERM]

Replace [SEARCH_TERM] with the relevant material (use + for spaces, e.g. 2x4+lumber, ceramic+tile, roofing+shingles).
Always include both links. This gives the customer real-time pricing with one click.
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
