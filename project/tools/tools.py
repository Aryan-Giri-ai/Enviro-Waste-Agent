"""
Tool Wrappers
Standard Python wrappers that worker agents use to access
external (or simulated) environments: an image classifier,
a disposal-rules search, an eco-impact calculator, and a
text summarizer.

NOTE: The Classifier and Search tools are implemented with
lightweight local heuristics/lookup tables so the whole system
runs end-to-end inside Colab without requiring external API
keys or network access. Swap in a real model/API call inside
ClassifierTool.classify() and SearchTool.search() when ready.
"""

import os
import random


MATERIAL_KEYWORDS = {
    "bottle": "PET plastic",
    "plastic": "mixed plastic",
    "bag": "LDPE plastic film",
    "can": "aluminum",
    "tin": "steel",
    "glass": "glass",
    "jar": "glass",
    "paper": "paper",
    "cardboard": "cardboard",
    "box": "cardboard",
    "battery": "alkaline battery",
    "electronic": "e-waste",
    "phone": "e-waste",
    "food": "organic waste",
    "banana": "organic waste",
    "styrofoam": "polystyrene foam",
    "foam": "polystyrene foam",
}

HAZARDOUS_MATERIALS = {"alkaline battery", "e-waste", "lithium battery", "chemical waste"}


class ClassifierTool:
    """Wraps an image classification API/model call."""

    def classify(self, image_path: str):
        """
        Identify waste item(s) in an image.
        Returns a list of {label, material, confidence, hazardous}.
        """
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
    "uncertain": "Material could not be confidently identified - when in doubt, place in general waste rather than contaminating recycling.",
}


class SearchTool:
    """Wraps a web search / database lookup for local disposal rules."""

    def search(self, location: str, material: str):
        """Return localized (or general best-practice) disposal guidance for a material and location."""
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
    """Condenses longer text (e.g. municipal guideline pages) into bullets."""

    def summarize(self, text: str, max_bullets: int = 3):
        if not text:
            return []
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        return [f"- {s}." for s in sentences[:max_bullets]]
