# 🌍 ENVIRO-WASTE-AGENT

### AI-Powered Multi-Agent Waste Classification & Eco-Awareness Platform
**Track:** Agents for Good | **Architecture:** Planner → Worker → Evaluator

---

## 📋 Overview
**ENVIRO-WASTE-AGENT** is an interactive multi-agent system designed to visually identify, classify, and guide users on the correct, safe sorting and disposal of waste. In addition to physical sorting guidance, the agent quantifies the environmental impact of recycling these items and spreads awareness through contextual facts and tips.

The application is fully prepared to run locally or be deployed directly as a web application to **Hugging Face Spaces** using the Gradio SDK.

---

## 🤖 Multi-Agent Architecture
The project is built on the **Planner-Worker-Evaluator** design pattern:

- **Planner Agent:** Formulates the subtask sequence and orchestrates execution, passing parameters downstream to individual workers.
- **Workers:**
  - *Vision Classifier Worker:* Analyzes waste item descriptions (or image inputs) to identify materials and categories.
  - *Local Disposal Advisor:* Looks up guidelines (via Google/DuckDuckGo search) tailored to the user's location.
  - *Eco-Educator Worker:* Computes carbon offsets, degradation timelines, and highlights ecological facts.
- **Evaluator Agent:** Validates output safety (ensuring hazard warnings are clearly visible) and formatting before serving the final markdown report.

---

## 🗂️ Project Structure

```text
project/
  ├── agents/
  │   ├── planner.py               # Coordinates planning, dispatches subtasks
  │   ├── worker.py                # Implementations of Vision, Rules, and Eco workers
  │   └── evaluator.py             # Validates safety, tone, and final report assembly
  ├── tools/
  │   └── tools.py                 # Tool wrappers (Classifier, Search, Calculator)
  ├── memory/
  │   └── session_memory.py        # Handles short-term context and long-term user stats
  ├── core/
  │   ├── config.py                # Configuration and API key loading
  │   ├── context_engineering.py   # Prompt engineering templates and guardrails
  │   ├── observability.py         # JSON logs, traces, and latency metric captures
  │   └── a2a_protocol.py          # Message envelope serialization schemas
  ├── main_agent.py                # Entry wrapper exposing run_agent(user_input)
  ├── app.py                       # Gradio interface web frontend
  └── requirements.txt             # Required Python dependencies
```

---

## ⚙️ Quick Start

### 1. Installation
Clone the repository and install the dependencies:
```bash
pip install -r project/requirements.txt
```

### 2. Configure environment
Create a `.env` file in your workspace directory (or project folder) containing your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run Demo
To run a fast command-line test of the multi-agent orchestration pipeline:
```bash
python project/run_demo.py
```

### 4. Run Web Application
To boot up the interactive Gradio web application interface locally:
```bash
python project/app.py
```

---

## 🛡️ License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
