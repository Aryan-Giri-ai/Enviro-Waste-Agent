"""
Evaluator Agent
Reviews the Planner's aggregated output for safety and logical
consistency before it is rendered to the user.
"""

from project.core import a2a_protocol

UNSAFE_DISPOSAL_KEYWORDS = ["incinerate", "burn", "bury"]


class Evaluator:
    name = "evaluator"
    role = "evaluator"

    def __init__(self, logger=None):
        self.logger = logger

    def _log(self, step, **kwargs):
        if self.logger:
            self.logger.log_event(step, **kwargs)

    def evaluate(self, trace_id: str, aggregated: dict):
        """
        Runs the safety checklist and consistency checks.
        Returns (approved: bool, reasons: list[str]).
        """
        reasons = []

        hazardous_items = [i for i in aggregated.get("items", []) if i.get("hazardous")]
        if hazardous_items and "hazard_warning" not in aggregated:
            reasons.append("Hazardous item detected without an explicit hazard warning header.")

        for material, bullets in aggregated.get("instructions", {}).items():
            text = " ".join(bullets).lower() if isinstance(bullets, list) else str(bullets).lower()
            for keyword in UNSAFE_DISPOSAL_KEYWORDS:
                if keyword in text and ("battery" in material.lower() or "e-waste" in material.lower() or "chemical" in material.lower()):
                    reasons.append(
                        f"Unsafe disposal instruction ('{keyword}') found for hazardous material '{material}'."
                    )

        items_materials = {i["material"] for i in aggregated.get("items", [])}
        footprint_materials = {f["material"] for f in aggregated.get("footprints", [])}
        if items_materials and footprint_materials and not items_materials.issubset(footprint_materials):
            reasons.append("Mismatch between classified materials and eco-footprint materials.")

        approved = len(reasons) == 0
        self._log("evaluator_review", trace_id=trace_id, approved=approved, reasons=reasons)
        return approved, reasons

    def build_response(self, trace_id, sender, approved, reasons):
        return a2a_protocol.make_response(
            trace_id=trace_id,
            sender=self.name,
            receiver=sender,
            task="evaluate_report",
            result={"approved": approved, "reasons": reasons},
            success=approved,
        )
