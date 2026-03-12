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

# Business Info (Configurable via .env or defaults)
BUSINESS_NAME = os.environ.get("BUSINESS_NAME", "ACME Corporation Ltd.")
GST_NO = os.environ.get("GST_NO", "27AAAAA0000A1Z5")
VIEWER_USERNAME = os.environ.get("VIEWER_USERNAME", "admin_user")


# --------------- Groq Settings ---------------
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE = 0.2          # Why Low temp ? → deterministic JSON output (Less Variability)
GROQ_MAX_OUTPUT_TOKENS = 4096

# --------------- Logging Configuration ---------------
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_LEVEL = logging.INFO

logging.basicConfig(format=LOG_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger("flowledger")


def get_api_key(override: str | None = None) -> str | None:
    """
    Retrieve the Groq API key.

    Priority:
        1. Explicit override (e.g. from Streamlit sidebar input)
        2. GROQ_API_KEY environment variable / .env file

    Returns:
        The API key string, or None if not found.
    """
    if override and override.strip():
        return override.strip()
    return os.environ.get("GROQ_API_KEY")
