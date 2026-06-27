# Contributing to ENVIRO-WASTE-AGENT

Thank you for your interest in contributing to **ENVIRO-WASTE-AGENT**! We welcome contributions to improve waste classification accuracy, support new regions, optimize the multi-agent pipelines, and build a better user experience.

---

## 🤝 Code of Conduct
By participating in this project, you agree to maintain a respectful, welcoming, and collaborative environment.

## 🚀 How to Contribute

### 1. Report Bugs & Request Features
If you find a bug or have an idea for a feature, please search existing GitHub Issues to see if it's already reported. If not, open a new issue detailing:
- Steps to reproduce the bug.
- Expected vs. actual behavior.
- Relevant log output (with trace IDs if available).

### 2. Propose Changes (Pull Requests)
1. **Fork the Repository:** Create a personal fork on GitHub.
2. **Clone & Set Up:** Clone your fork locally and configure dependencies.
   ```bash
   git clone https://github.com/your-username/ENVIRO-WASTE-AGENT.git
   cd ENVIRO-WASTE-AGENT
   pip install -r requirements.txt
   ```
3. **Create a Branch:** Create a branch for your work.
   ```bash
   git checkout -b feature/amazing-new-worker
   ```
4. **Make and Test Changes:** Ensure all local tests pass.
   ```bash
   python project/run_demo.py
   ```
5. **Commit & Push:** Commit your changes using descriptive commit messages and push them to your fork.
6. **Open a Pull Request:** Submit a Pull Request (PR) to the `main` branch of the parent repository.

---

## 🛠️ Development Guidelines
- **Multi-Agent Patterns:** Respect the Planner-Worker-Evaluator architecture. Do not bypass the Evaluator agent for client delivery.
- **Safety First:** Never suggest burning, burying, or dumping hazardous waste. Always ensure the safety check in `evaluator.py` passes.
- **A2A Protocol compliance:** Use the `A2AMessage` model for any communication payloads between agents.
- **Clean Imports:** Ensure absolute pathing is used inside the `project/` directory package structure.
