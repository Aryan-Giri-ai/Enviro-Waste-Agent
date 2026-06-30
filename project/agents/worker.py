"""
Worker Agents
Implementations of the Vision Classifier, Local Disposal Advisor,
and Eco-Educator workers. Each worker receives an A2A request
envelope from the Planner and returns an A2A response envelope.
"""

from project.core import a2a_protocol
from project.core.context_engineering import build_context
from project.tools.tools import ClassifierTool, SearchTool, EcoCalculatorTool, SummarizerTool


class BaseWorker:
    name = "base_worker"
    role = "base"

    def __init__(self, logger=None):
        self.logger = logger

    def _log(self, step, **kwargs):
        if self.logger:
            self.logger.log_event(step, **kwargs)

    def handle_request(self, request_envelope: dict) -> dict:
        raise NotImplementedError


class VisionClassifierWorker(BaseWorker):
    name = "vision_worker"
    role = "vision_worker"

    def __init__(self, logger=None, classifier_tool: ClassifierTool = None):
        super().__init__(logger)
        self.classifier_tool = classifier_tool or ClassifierTool()

    def handle_request(self, request_envelope: dict) -> dict:
        trace_id = request_envelope["trace_id"]
        params = request_envelope["payload"].get("parameters", {})
        image_path = params.get("image_path")
        text_description = params.get("text_description")

        context = build_context(self.role, {"image_path": image_path, "text_description": text_description})
        self._log("vision_worker_start", trace_id=trace_id, image_path=image_path, text_description=text_description)

        items = self.classifier_tool.classify(image_path, text_description=text_description)

        self._log("vision_worker_end", trace_id=trace_id, items=items)

        return a2a_protocol.make_response(
            trace_id=trace_id,
            sender=self.name,
            receiver=request_envelope["sender"],
            task=request_envelope["payload"].get("task", "classify_waste_image"),
            result={"items": items, "context_used": context["system_prompt"]},
        )


class LocalDisposalWorker(BaseWorker):
    name = "rules_worker"
    role = "rules_worker"

    def __init__(self, logger=None, search_tool: SearchTool = None, summarizer_tool: SummarizerTool = None):
        super().__init__(logger)
        self.search_tool = search_tool or SearchTool()
        self.summarizer_tool = summarizer_tool or SummarizerTool()

    def handle_request(self, request_envelope: dict) -> dict:
        trace_id = request_envelope["trace_id"]
        params = request_envelope["payload"].get("parameters", {})
        location = params.get("location")
        materials = params.get("materials", [])

        self._log("rules_worker_start", trace_id=trace_id, location=location, materials=materials)

        instructions = {}
        for material in materials:
            raw_rule = self.search_tool.search(location, material)
            instructions[material] = self.summarizer_tool.summarize(raw_rule, max_bullets=2)

        self._log("rules_worker_end", trace_id=trace_id, instructions=instructions)

        return a2a_protocol.make_response(
            trace_id=trace_id,
            sender=self.name,
            receiver=request_envelope["sender"],
            task=request_envelope["payload"].get("task", "lookup_disposal_rules"),
            result={"location": location, "instructions": instructions},
        )


class EcoEducatorWorker(BaseWorker):
    name = "eco_worker"
    role = "eco_worker"

    def __init__(self, logger=None, eco_calculator: EcoCalculatorTool = None):
        super().__init__(logger)
        self.eco_calculator = eco_calculator or EcoCalculatorTool()

    def handle_request(self, request_envelope: dict) -> dict:
        trace_id = request_envelope["trace_id"]
        params = request_envelope["payload"].get("parameters", {})
        materials = params.get("materials", [])
        weight_kg = params.get("weight_kg", 0.1)

        self._log("eco_worker_start", trace_id=trace_id, materials=materials)

        footprints = [self.eco_calculator.calculate(m, weight_kg) for m in materials]
        tip = self._build_awareness_tip(footprints)

        self._log("eco_worker_end", trace_id=trace_id, footprints=footprints)

        return a2a_protocol.make_response(
            trace_id=trace_id,
            sender=self.name,
            receiver=request_envelope["sender"],
            task=request_envelope["payload"].get("task", "calculate_eco_footprint"),
            result={"footprints": footprints, "awareness_tip": tip},
        )

    @staticmethod
    def _build_awareness_tip(footprints):
        total_offset = sum(f["carbon_offset_kg_if_recycled"] for f in footprints)
        if total_offset > 0:
            return (
                f"Recycling these items correctly could save roughly "
                f"{round(total_offset, 2)} kg of CO2-equivalent emissions."
            )
        return "Recycling correctly keeps contaminants out of the waste stream, even when carbon savings are minimal."
