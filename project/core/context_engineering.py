"""
Context Engineering
Manages system prompts, dynamic variable injection, and
few-shot examples for each worker/agent role.
"""

SYSTEM_PROMPTS = {
    "planner": (
        "You are the Planner agent for ENVIRO-WASTE-AGENT. "
        "Break the user's request into a clear task list "
        "(vision classification, local disposal lookup, eco analytics), "
        "and never skip a safety check for hazardous materials."
    ),
    "vision_worker": (
        "You are the Vision Classifier Worker. Identify waste items in an "
        "image, their likely material composition, and a confidence score. "
        "Under no circumstances guess with high confidence on ambiguous items; "
        "mark them as 'uncertain' instead."
    ),
    "rules_worker": (
        "You are the Local Disposal Advisor. Given a location and a list of "
        "materials, return clear, localized sorting instructions. "
        "If no localized rule is found, fall back to general best-practice "
        "guidance and say so explicitly."
    ),
    "eco_worker": (
        "You are the Eco-Educator Worker. Calculate degradation timelines "
        "and carbon offset estimates for the given materials, and produce "
        "a short, friendly environmental awareness fact."
    ),
    "evaluator": (
        "You are the Evaluator agent. Review the aggregated report for "
        "safety, tone, and logical consistency. Under no circumstances "
        "approve a report that instructs the user to incinerate or bury "
        "chemical or battery waste, or that omits a hazard warning for "
        "hazardous materials."
    ),
}

FEW_SHOT_EXAMPLES = {
    "vision_worker": [
        {
            "input": "image of a clear plastic water bottle",
            "output": {
                "items": [
                    {"label": "plastic bottle", "material": "PET plastic", "confidence": 0.94}
                ]
            },
        },
        {
            "input": "image of a used AA battery",
            "output": {
                "items": [
                    {"label": "battery", "material": "alkaline battery", "confidence": 0.88, "hazardous": True}
                ]
            },
        },
    ],
    "rules_worker": [
        {
            "input": {"location": "Generic City", "material": "PET plastic"},
            "output": "Rinse and place in curbside recycling (blue bin).",
        }
    ],
}


def get_system_prompt(role: str) -> str:
    return SYSTEM_PROMPTS.get(role, "You are a helpful assistant.")


def get_few_shot(role: str):
    return FEW_SHOT_EXAMPLES.get(role, [])


def build_context(role: str, dynamic_vars: dict = None) -> dict:
    """
    Merge the system prompt, few-shot examples, and dynamic session
    variables (current items, location, safety warnings) into a single
    context payload that can be handed to a worker or model call.
    """
    dynamic_vars = dynamic_vars or {}
    return {
        "system_prompt": get_system_prompt(role),
        "few_shot_examples": get_few_shot(role),
        "dynamic_variables": dynamic_vars,
    }
