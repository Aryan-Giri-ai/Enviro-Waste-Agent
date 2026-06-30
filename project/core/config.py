"""
Central Configuration
Single source of truth for the Gemini API key and model name.

Notes:
  - Key name is GOOGLE_API_KEY — matches the secret set in Google Colab's
    userdata sidebar and any HF Spaces / .env configuration.
  - load_dotenv() is called so a local .env file is actually loaded.
  - Model is gemini-2.5-flash-lite (gemini-1.5-flash was retired).
  - SDK: use `google-genai` (google-generativeai was deprecated Nov 2025).
"""

import os
import warnings
from dotenv import load_dotenv

# Load .env from the working directory (or any parent) into os.environ.
# This must happen before any os.getenv() call.
load_dotenv()

try:
    # Google Colab: read from the Colab Secrets sidebar.
    from google.colab import userdata  # type: ignore
    GOOGLE_API_KEY: str = userdata.get("GOOGLE_API_KEY") or ""
except (ImportError, Exception):
    # Local / HF Spaces: read from environment (populated by load_dotenv above
    # or by the host's Secrets / environment variables).
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

# Current active Gemini model (2.5 generation).
# gemini-1.5-flash and all 1.x models were retired by Google.
GEMINI_MODEL_NAME: str = "gemini-2.5-flash-lite"

if not GOOGLE_API_KEY:
    warnings.warn(
        "GOOGLE_API_KEY is not set. "
        "Tools will run in local-heuristic fallback mode. "
        "Set it in a .env file, as an environment variable, or in Colab Secrets.",
        RuntimeWarning,
        stacklevel=2,
    )
