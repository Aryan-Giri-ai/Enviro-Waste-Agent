"""
Tool Wrappers
Standard Python wrappers that worker agents use to access
external (or simulated) environments: an image classifier,
a disposal-rules search, an eco-impact calculator, and a
text summarizer.

Gemini integration:
  - ClassifierTool, SearchTool, SummarizerTool each attempt a Gemini
    API call first (using google-genai SDK + GOOGLE_API_KEY from config).
  - If the key is absent, empty, or the API call fails for any reason
    (quota, network, etc.) the tool falls back transparently to the
    local heuristic already implemented here.
  - EcoCalculatorTool is purely local and requires no API.
"""

import os
import json
import random
import warnings

from project.core.config import GOOGLE_API_KEY, GEMINI_MODEL_NAME
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Structured Output Schemas for Gemini API
# ---------------------------------------------------------------------------
class WasteItem(BaseModel):
    label: str = Field(description="Name/description of the item (e.g. plastic bottle, apple core)")
    material: str = Field(description="Material type from choices: PET plastic, mixed plastic, LDPE plastic film, aluminum, steel, glass, paper, cardboard, alkaline battery, e-waste, organic waste, polystyrene foam, uncertain")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    hazardous: bool = Field(description="Whether the item is hazardous waste or e-waste")

class ClassificationResult(BaseModel):
    items: list[WasteItem] = Field(description="List of detected waste items in the image")

# ---------------------------------------------------------------------------
# Gemini client — initialised once at module load.
# Uses the new `google-genai` SDK (google-generativeai was deprecated Nov 2025).
# ---------------------------------------------------------------------------
_gemini_client = None
_gemini_model = None
_genai_types = None


if GOOGLE_API_KEY:
    try:
        from google import genai as _genai_lib          # google-genai SDK
        from google.genai import types as _genai_types_mod
        _gemini_client = _genai_lib.Client(api_key=GOOGLE_API_KEY)
        _gemini_model = GEMINI_MODEL_NAME
        _genai_types = _genai_types_mod
    except ImportError:

        warnings.warn(
            "google-genai package not found. "
            "Install it with: pip install google-genai\n"
            "Falling back to local heuristics.",
            RuntimeWarning,
            stacklevel=1,
        )
    except Exception as exc:
        warnings.warn(
            f"Gemini client initialisation failed ({exc}). "
            "Falling back to local heuristics.",
            RuntimeWarning,
            stacklevel=1,
        )


def _gemini_generate(prompt: str) -> str:
    """
    Send a text prompt to Gemini and return the response text.
    Raises an exception if the client is not available or the call fails.
    """
    if _gemini_client is None:
        raise RuntimeError("Gemini client is not initialised.")
    response = _gemini_client.models.generate_content(
        model=_gemini_model,
        contents=prompt,
    )
    return response.text


MATERIAL_KEYWORDS = {
    # --- Metal (Aluminum and Steel) ---
    "can": "aluminum",
    "cans": "aluminum",
    "foil": "aluminum",
    "engine": "steel",
    "gear": "steel",
    "gears": "steel",
    "plate": "steel",
    "plates": "steel",
    "wire": "steel",
    "pipe": "steel",
    "scrap metal": "steel",
    "nail": "steel",
    "screw": "steel",
    "bolt": "steel",
    
    # --- Organic (Food, Garden, and Wood Waste) ---
    "leaf": "organic waste",
    "leaves": "organic waste",
    "dry leaves": "organic waste",
    "stump": "organic waste",
    "tree stumps": "organic waste",
    "wood": "organic waste",
    "wooden": "organic waste",
    "branch": "organic waste",
    "bark": "organic waste",
    "scrap": "organic waste",
    "scraps": "organic waste",
    "vegetable scraps": "organic waste",
    "rotten": "organic waste",
    "rotten food": "organic waste",
    "apple": "organic waste",
    "core": "organic waste",
    "peel": "organic waste",
    "orange": "organic waste",
    "bread": "organic waste",
    "coffee": "organic waste",
    "tea": "organic waste",
    "banana": "organic waste",
    "food": "organic waste",
    
    # --- Plastics / Film / Foam ---
    "bottle": "PET plastic",
    "plastic": "mixed plastic",
    "cup": "mixed plastic",
    "container": "mixed plastic",
    "tub": "mixed plastic",
    "bag": "LDPE plastic film",
    "wrap": "LDPE plastic film",
    "shrink wrap": "LDPE plastic film",
    "bubble wrap": "LDPE plastic film",
    "styrofoam": "polystyrene foam",
    "foam": "polystyrene foam",
    "tray": "polystyrene foam",
    "cup_foam": "polystyrene foam",
    
    # --- Paper / Cardboard ---
    "paper": "paper",
    "newspaper": "paper",
    "magazine": "paper",
    "mail": "paper",
    "envelope": "paper",
    "book": "paper",
    "cardboard": "cardboard",
    "box": "cardboard",
    "carton": "cardboard",
    "tetra": "cardboard",
    
    # --- E-Waste ---
    "electronic": "e-waste",
    "phone": "e-waste",
    "laptop": "e-waste",
    "computer": "e-waste",
    "monitor": "e-waste",
    "tv": "e-waste",
    "television": "e-waste",
    "screen": "e-waste",
    "cable": "e-waste",
    "charger": "e-waste",
    "keyboard": "e-waste",
    "mouse": "e-waste",
    "printer": "e-waste",
    "circuit": "e-waste",
    
    # --- Batteries & Chemicals ---
    "battery": "alkaline battery",
    "batteries": "alkaline battery",
    "paint": "chemical waste",
    "solvent": "chemical waste",
    "chemical": "chemical waste",
    "pesticide": "chemical waste",
    "oil": "chemical waste",
    "thermometer": "chemical waste",
}

HAZARDOUS_MATERIALS = {"alkaline battery", "e-waste", "lithium battery", "chemical waste"}


class ClassifierTool:
    """Wraps an image classification API/model call.

    Primary:  Gemini multimodal API (describes the waste item from a file path).
    Fallback: Filename-keyword heuristic (original behaviour).
    """

    def classify(self, image_path: str):
        """
        Identify waste item(s) in an image.
        Returns a list of {label, material, confidence, hazardous}.
        """
        # --- Primary: Gemini API ---
        if _gemini_client and image_path and os.path.isfile(image_path):
            try:
                from PIL import Image as PIL_Image
                # Open the actual image file to send to Gemini
                img = PIL_Image.open(image_path)
                
                prompt = (
                    "You are a waste classification expert. Look at this image of waste items.\n"
                    "Identify the most likely waste item(s) present in the image. "
                    "Classify each item's material type exactly into one of the allowed categories: "
                    "PET plastic, mixed plastic, LDPE plastic film, aluminum, steel, glass, paper, "
                    "cardboard, alkaline battery, e-waste, organic waste, polystyrene foam, uncertain."
                )
                
                # Use structured outputs if supported by the SDK environment
                if _genai_types is not None:
                    config = _genai_types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ClassificationResult,
                    )
                    response = _gemini_client.models.generate_content(
                        model=_gemini_model,
                        contents=[img, prompt],
                        config=config,
                    )
                    raw = response.text
                    data = json.loads(raw)
                    raw_items = data.get("items", [])
                else:
                    # Raw JSON fallback prompting
                    json_prompt = (
                        prompt + "\nRespond ONLY with a valid JSON object matching this schema:\n"
                        '{"items": [{"label": "string", "material": "string", "confidence": float, "hazardous": boolean}]}'
                    )
                    response = _gemini_client.models.generate_content(
                        model=_gemini_model,
                        contents=[img, json_prompt],
                    )
                    raw = response.text
                    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                    data = json.loads(raw)
                    raw_items = data.get("items", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

                # Normalise and structure results
                items = []
                for item in raw_items:
                    if not isinstance(item, dict):
                        continue
                    mat = item.get("material", "uncertain")
                    items.append({
                        "label": item.get("label", "waste item"),
                        "material": mat,
                        "confidence": float(item.get("confidence", 0.8)),
                        "hazardous": mat in HAZARDOUS_MATERIALS,
                    })
                return items
            except Exception as exc:
                warnings.warn(
                    f"ClassifierTool Gemini call failed ({exc}). Using local fallback.",
                    RuntimeWarning,
                    stacklevel=2,
                )

        # --- Fallback: filename-keyword heuristic (original behaviour) ---
        filename = os.path.basename(image_path).lower() if image_path else ""
        matches = [
            (keyword, material)
            for keyword, material in MATERIAL_KEYWORDS.items()
            if keyword in filename
        ]

        if not matches:
            return [
                {
                    "label": "unidentified item",
                    "material": "uncertain",
                    "confidence": 0.35,
                    "hazardous": False,
                }
            ]

        results = []
        for keyword, material in matches:
            results.append(
                {
                    "label": keyword,
                    "material": material,
                    "confidence": round(random.uniform(0.80, 0.97), 2),
                    "hazardous": material in HAZARDOUS_MATERIALS,
                }
            )
        return results


LOCAL_RULES_DB = {
    "PET plastic": "Rinse and place in curbside recycling (blue bin).",
    "mixed plastic": "Check the resin code; most #1/#2 plastics go in recycling, others go to general waste.",
    "LDPE plastic film": "Plastic bags/film usually cannot go in curbside recycling - return to a store drop-off point.",
    "aluminum": "Rinse and place in curbside recycling (blue bin).",
    "steel": "Rinse and place in curbside recycling (blue bin).",
    "glass": "Rinse and place in curbside recycling (glass bin); remove caps/lids.",
    "paper": "Keep dry and place in paper recycling.",
    "cardboard": "Flatten and place in cardboard/paper recycling.",
    "alkaline battery": "Do NOT place in household trash or recycling. Drop off at a designated battery/e-waste collection point.",
    "e-waste": "Do NOT place in household trash. Take to an authorized e-waste recycling center.",
    "organic waste": "Place in compost/organic waste bin if available, otherwise general waste.",
    "polystyrene foam": "Most municipal programs do NOT recycle foam; place in general waste or a specialty drop-off.",
    "chemical waste": "⚠️ WARNING: Hazardous chemical. Do NOT place in household trash or recycling, and do NOT pour down drains. Bring to a local household hazardous waste (HHW) depot.",
    "uncertain": "Material could not be confidently identified - when in doubt, place in general waste rather than contaminating recycling.",
}


class SearchTool:
    """Wraps a web search / database lookup for local disposal rules.

    Primary:  Gemini API — generates location-aware disposal guidance.
    Fallback: LOCAL_RULES_DB static dictionary (original behaviour).
    """

    def search(self, location: str, material: str):
        """Return localized (or general best-practice) disposal guidance for a material and location."""
        # --- Primary: Gemini API ---
        if _gemini_client:
            try:
                location_ctx = f"The user is located in: {location}." if location else "Location is unknown; provide general global best-practice guidance."
                prompt = (
                    f"You are a waste disposal expert. {location_ctx}\n"
                    f"Provide clear, safe, practical disposal instructions for this material: {material}.\n"
                    "Rules: NEVER suggest incineration, burning, burying, or illegal dumping. "
                    "If hazardous (battery, e-waste, chemical), explicitly say to take to a certified disposal centre.\n"
                    "Keep the response under 60 words. Return plain text only, no markdown."
                )
                return _gemini_generate(prompt).strip()
            except Exception as exc:
                warnings.warn(
                    f"SearchTool Gemini call failed ({exc}). Using local fallback.",
                    RuntimeWarning,
                    stacklevel=2,
                )

        # --- Fallback: static lookup table (original behaviour) ---
        rule = LOCAL_RULES_DB.get(material, LOCAL_RULES_DB["uncertain"])
        if location:
            note = f"(General guidance shown - localized rules for '{location}' were not found in this demo lookup table.)"
        else:
            note = "(No location provided - showing general best-practice guidance.)"
        return f"{rule} {note}"


DECOMPOSITION_YEARS = {
    "PET plastic": 450,
    "mixed plastic": 400,
    "LDPE plastic film": 20,
    "aluminum": 200,
    "steel": 50,
    "glass": 1000000,
    "paper": 0.05,
    "cardboard": 0.2,
    "alkaline battery": 100,
    "e-waste": 1000,
    "organic waste": 0.1,
    "polystyrene foam": 500,
    "chemical waste": 100,
    "uncertain": None,
}

CARBON_OFFSET_KG_PER_KG = {
    "PET plastic": 1.5,
    "mixed plastic": 1.2,
    "LDPE plastic film": 1.0,
    "aluminum": 9.0,
    "steel": 1.8,
    "glass": 0.3,
    "paper": 0.9,
    "cardboard": 0.8,
    "alkaline battery": 0.0,
    "e-waste": 0.0,
    "organic waste": 0.5,
    "polystyrene foam": 0.0,
    "chemical waste": 0.0,
    "uncertain": 0.0,
}


class EcoCalculatorTool:
    """Python logic for decomposition timelines and carbon coefficients."""

    def calculate(self, material: str, weight_kg: float = 0.1):
        years = DECOMPOSITION_YEARS.get(material, None)
        offset = CARBON_OFFSET_KG_PER_KG.get(material, 0.0) * weight_kg

        if years is None:
            decomposition_text = "unknown decomposition timeline"
        elif years >= 1000:
            decomposition_text = f"~{years:,.0f} years (essentially does not biodegrade)"
        elif years < 1:
            decomposition_text = f"~{int(years * 365)} days"
        else:
            decomposition_text = f"~{years} years"

        return {
            "material": material,
            "estimated_weight_kg": weight_kg,
            "decomposition_estimate": decomposition_text,
            "carbon_offset_kg_if_recycled": round(offset, 3),
        }


class SummarizerTool:
    """Condenses longer text (e.g. municipal guideline pages) into bullets.

    Primary:  Gemini API — produces polished, context-aware bullet points.
    Fallback: Sentence-splitting heuristic (original behaviour).
    """

    def summarize(self, text: str, max_bullets: int = 3):
        if not text:
            return []

        # --- Primary: Gemini API ---
        if _gemini_client:
            try:
                prompt = (
                    f"Summarise the following waste disposal guidance into at most {max_bullets} "
                    "concise, actionable bullet points. "
                    "Do NOT suggest burning, incineration, burying, or illegal dumping. "
                    "Return ONLY bullet points starting with '- ', one per line, no additional text.\n\n"
                    f"{text}"
                )
                raw = _gemini_generate(prompt).strip()
                bullets = [line.strip() for line in raw.splitlines() if line.strip().startswith("-")]
                return bullets[:max_bullets] if bullets else self._local_summarize(text, max_bullets)
            except Exception as exc:
                warnings.warn(
                    f"SummarizerTool Gemini call failed ({exc}). Using local fallback.",
                    RuntimeWarning,
                    stacklevel=2,
                )

        # --- Fallback: sentence-splitting heuristic (original behaviour) ---
        return self._local_summarize(text, max_bullets)

    def _local_summarize(self, text: str, max_bullets: int) -> list:
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        return [f"- {s}." for s in sentences[:max_bullets]]
