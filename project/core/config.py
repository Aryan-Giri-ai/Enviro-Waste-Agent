"""
Central Configuration
Handles API keys and global settings.
"""

import os
try:
    from google.colab import userdata
    GOOGLE_API_KEY = userdata.get('GOOGLE_API_KEY')
except (ImportError, Exception):
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

GEMINI_MODEL_NAME = "gemini-1.5-flash"
