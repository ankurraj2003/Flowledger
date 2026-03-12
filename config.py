"""
=============================================================
Handles API keys, environment variables, and constants(project wide). Loads from .env file or system environment.
=============================================================
"""

import os
import logging
from dotenv import load_dotenv

# --------------- Load .env if present ---------------
load_dotenv()

# --------------- Application Metadata ---------------
APP_TITLE = "Flowledger"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = (
    "AI-driven middleware that converts unstructured "
    "Purchase Orders (PDFs) into structured ERP data."
)

# --------------- Google Gemini Settings ---------------
GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_TEMPERATURE = 0.2          # Why Low temp ? → deterministic JSON output (Less Variability)
GEMINI_MAX_OUTPUT_TOKENS = 4096

# --------------- Logging Configuration ---------------
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_LEVEL = logging.INFO

logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger("flowledger")


def get_api_key(override: str | None = None) -> str | None:
    """
    Retrieve the Google API key.

    Priority:
        1. Explicit override (e.g. from Streamlit sidebar input)
        2. GOOGLE_API_KEY environment variable / .env file

    Returns:
        The API key string, or None if not found.
    """
    if override and override.strip():
        return override.strip()
    return os.environ.get("GEMINI_API_KEY")
