"""
Planner Agent
Parses user input, builds a step-by-step execution plan, dispatches
tasks to the worker agents via the A2A protocol, and compiles the
intermediate results for the Evaluator.
"""

from project.core import a2a_protocol
from project.core.context_engineering import build_context
from project.agents.worker import VisionClassifierWorker, LocalDisposalWorker, EcoEducatorWorker


class Planner:
    name = "planner"
    role = "planner"

    def __init__(self, logger=None):
        self.logger = logger
        self.vision_worker = VisionClassifierWorker(logger=logger)
        self.rules_worker = LocalDisposalWorker(logger=logger)
        self.eco_worker = EcoEducatorWorker(logger=logger)

    def _log(self, step, **kwargs):
        if self.logger:
            self.logger.log_event(step, **kwargs)

    def create_plan(self, trace_id: str, image_path: str = None, location: str = None):
        """Builds an ordered task list for this request."""
        plan = []
        if image_path:
            plan.append({"task": "classify_waste_image", "worker": "vision_worker"})
        plan.append({"task": "lookup_disposal_rules", "worker": "rules_worker"})
        plan.append({"task": "calculate_eco_footprint", "worker": "eco_worker"})
        self._log("planner_create_plan", trace_id=trace_id, plan=plan)
        return plan

    def run(self, trace_id: str, image_path: str = None, location: str = None, weight_kg: float = 0.1):
        """
        Executes the full plan: Vision -> Rules -> Eco, then returns
        an aggregated results dict ready for the Evaluator.
        """
        context = build_context(self.role, {"image_path": image_path, "location": location})
        self._log("planner_start", trace_id=trace_id, context=context["system_prompt"])

        plan = self.create_plan(trace_id, image_path, location)
        aggregated = {"items": [], "materials": [], "instructions": {}, "footprints": [], "awareness_tip": ""}

        vision_request = a2a_protocol.make_request(
            trace_id=trace_id,
            sender=self.name,
            receiver=self.vision_worker.name,
            task="classify_waste_image",
            parameters={"image_path": image_path},
        )
        vision_response = self.vision_worker.handle_request(vision_request)
        items = vision_response["payload"]["result"]["items"]
        materials = sorted({item["material"] for item in items})
        aggregated["items"] = items
        aggregated["materials"] = materials

        rules_request = a2a_protocol.make_request(
            trace_id=trace_id,
            sender=self.name,
            receiver=self.rules_worker.name,
            task="lookup_disposal_rules",
            parameters={"location": location, "materials": materials},
        )
        rules_response = self.rules_worker.handle_request(rules_request)
        aggregated["instructions"] = rules_response["payload"]["result"]["instructions"]

        eco_request = a2a_protocol.make_request(
            trace_id=trace_id,
            sender=self.name,
            receiver=self.eco_worker.name,
            task="calculate_eco_footprint",
            parameters={"materials": materials, "weight_kg": weight_kg},
        )
        eco_response = self.eco_worker.handle_request(eco_request)
        aggregated["footprints"] = eco_response["payload"]["result"]["footprints"]
        aggregated["awareness_tip"] = eco_response["payload"]["result"]["awareness_tip"]

        self._log("planner_aggregated", trace_id=trace_id, aggregated=aggregated)
        return plan, aggregated

    def refine(self, trace_id: str, aggregated: dict, rejection_reasons: list):
        """
        Called by MainAgent when the Evaluator rejects a report.
        Applies simple corrective rules (e.g. force a hazard warning)
        and returns the corrected aggregated package.
        """
        self._log("planner_refine", trace_id=trace_id, reasons=rejection_reasons)
        for item in aggregated.get("items", []):
            if item.get("hazardous") and "hazard_warning" not in aggregated:
                aggregated["hazard_warning"] = (
                    "WARNING: One or more items are hazardous waste. "
                    "Do NOT place them in household trash, recycling, or compost. "
                    "Take them to an authorized hazardous-waste or e-waste collection point."
                )
        return aggregated
