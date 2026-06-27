"""
Gradio UI application entry point for ENVIRO-WASTE-AGENT.
"""

import gradio as gr

from project.main_agent import MainAgent

agent = MainAgent()


def process(image, location, message):
    image_path = image if isinstance(image, str) else None
    result = agent.handle_message(user_input=message or "", image_path=image_path, location=location or None)
    return result["response"]


def build_interface():
    with gr.Blocks(title="ENVIRO-WASTE-AGENT") as demo:
        gr.Markdown(
            "# ENVIRO-WASTE-AGENT\n"
            "Upload a waste image to get classification, sorting instructions, and its eco footprint."
        )
        with gr.Row():
            image_input = gr.Image(type="filepath", label="Upload waste image")
            with gr.Column():
                location_input = gr.Textbox(label="Location (optional)", placeholder="e.g. Springfield, IL")
                message_input = gr.Textbox(label="Message (optional)", placeholder="Anything you'd like to ask the agent")
        submit_btn = gr.Button("Analyze")
        output = gr.Markdown(label="Report")

        submit_btn.click(fn=process, inputs=[image_input, location_input, message_input], outputs=output)

    return demo


if __name__ == "__main__":
    interface = build_interface()
    interface.launch()
