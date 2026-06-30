"""
Main Agent
Wrapper coordination agent that the frontend (app.py) talks to.
Owns the session, drives the Planner -> Evaluator refinement loop,
and renders the final markdown report.
"""

from project.agents.planner import Planner
from project.agents.evaluator import Evaluator
from project.memory.session_memory import SessionMemory, UserProfileMemory
from project.core.observability import TraceLogger
from project.core import a2a_protocol

MAX_REFINEMENT_LOOPS = 2


class MainAgent:
    def __init__(self, user_id: str = "default_user"):
        self.logger = TraceLogger()
        self.planner = Planner(logger=self.logger)
        self.evaluator = Evaluator(logger=self.logger)
        self.session = SessionMemory()
        self.profile = UserProfileMemory(user_id=user_id)

    def handle_message(self, user_input: str, image_path: str = None, location: str = None, weight_kg: float = 0.1):
        """
        Main entry point. Accepts a free-text user_input plus optional
        image_path/location, runs the full agent pipeline, and returns
        {"response": <markdown str>, "trace_id": ..., "approved": bool}.
        """
        trace_id = a2a_protocol.new_trace_id()
        self.logger.trace_id = trace_id
        self.session.set_input(image_metadata=image_path, location_query=location)

        # Normalise user input to check for simple greetings / help triggers
        greetings = {"hello", "hi", "hey", "help", "start", "welcome", "test", "demo"}
        cleaned_input = user_input.strip().lower().rstrip("!?.")
        is_greeting = cleaned_input in greetings or len(user_input.split()) <= 2 and cleaned_input == ""

        if is_greeting and not image_path:
            welcome_text = self._handle_welcome_message()
            self.session.set_final_report(welcome_text)
            return {"response": welcome_text, "trace_id": trace_id, "approved": True}

        # Run the full multi-agent sorting and classification pipeline (multimodal or text-only)
        plan, aggregated = self.planner.run(
            trace_id,
            image_path=image_path,
            text_description=user_input,
            location=location,
            weight_kg=weight_kg
        )
        self.session.set_task_list(plan)
        self.session.store_worker_response("aggregated", aggregated)

        approved, reasons = self.evaluator.evaluate(trace_id, aggregated)
        loops = 0
        while not approved and loops < MAX_REFINEMENT_LOOPS:
            aggregated = self.planner.refine(trace_id, aggregated, reasons)
            self.session.add_evaluator_review({"approved": approved, "reasons": reasons})
            approved, reasons = self.evaluator.evaluate(trace_id, aggregated)
            loops += 1

        self.session.add_evaluator_review({"approved": approved, "reasons": reasons})

        for f in aggregated.get("footprints", []):
            self.profile.record_sorted_item(carbon_offset_kg=f.get("carbon_offset_kg_if_recycled", 0.0))

        report = self._render_report(aggregated, approved, reasons)
        self.session.set_final_report(report)

        return {"response": report, "trace_id": trace_id, "approved": approved}

    def _handle_welcome_message(self) -> str:
        return (
            "👋 Hello! I'm the **ENVIRO-WASTE-AGENT**.\n\n"
            "I can help you sort waste and show you environmental statistics. You can:\n"
            "1. **Upload an image** of the waste items.\n"
            "2. **Type a list of items** directly in the text box (e.g. *'broken laptop, paint can, glass jar'*).\n"
            "3. **Do both** (upload an image and add text context).\n\n"
            "Optionally, provide your location (e.g. *'Seattle, USA'*) for localized municipal guidelines!"
        )

    def _render_report(self, aggregated: dict, approved: bool, reasons: list) -> str:
        lines = ["# ENVIRO-WASTE-AGENT Report\n"]

        if aggregated.get("hazard_warning"):
            lines.append(f"> WARNING: **{aggregated['hazard_warning']}**\n")

        lines.append("## Identified Items")
        for item in aggregated.get("items", []):
            hazard_tag = " [HAZARDOUS]" if item.get("hazardous") else ""
            lines.append(
                f"- **{item['label']}** -> material: `{item['material']}` "
                f"(confidence: {item['confidence']:.0%}){hazard_tag}"
            )

        lines.append("\n## Sorting Instructions")
        for material, bullets in aggregated.get("instructions", {}).items():
            lines.append(f"**{material}:**")
            for b in bullets:
                lines.append(f"  {b}")

        lines.append("\n## Ecological Footprint")
        for fp in aggregated.get("footprints", []):
            lines.append(
                f"- {fp['material']}: decomposition {fp['decomposition_estimate']}, "
                f"carbon savings if recycled ~= {fp['carbon_offset_kg_if_recycled']} kg CO2e"
            )

        if aggregated.get("awareness_tip"):
            lines.append(f"\nTIP: *{aggregated['awareness_tip']}*")

        lines.append(f"\n---\n_Evaluator status: {'approved' if approved else 'approved with caveats'}_")
        if reasons:
            lines.append("_Notes: " + "; ".join(reasons) + "_")

        return "\n".join(lines)


def run_agent(user_input: str):
    agent = MainAgent()
    result = agent.handle_message(user_input)
    return result["response"]
