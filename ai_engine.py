"""
=============================================================
Sends extracted PDF text to Google Gemini with a strictly
defined JSON schema prompt.  Parses and validates the
structured response.  Uses the new google-genai SDK.
=============================================================
"""

import json
import re
import logging
from groq import Groq
from config import GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_OUTPUT_TOKENS
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("flowledger.ai_engine")

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1.5, min=2, max=15), reraise=True)
def _generate_with_retry(client, prompt):
    logger.info("Calling Groq API...")
    return client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=GROQ_TEMPERATURE,
        max_tokens=GROQ_MAX_OUTPUT_TOKENS,
        response_format={"type": "json_object"}
    )


class AIAnalysisError(Exception):
    """Raised when Groq analysis fails."""
    pass


# ─── System prompt that enforces strict JSON output ──────────
EXTRACTION_PROMPT = """You are an expert Invoice / Purchase Order data extraction engine.

Analyze the following document text and extract structured data in **strict JSON** format.

### REQUIRED JSON SCHEMA:
```json
{{
    "vendor_name": "string — company/vendor name issuing the invoice",
    "vendor_address": "string — full vendor address",
    "date": "string — invoice/document date in YYYY-MM-DD format",
    "due_date": "string — payment due date in YYYY-MM-DD format",
    "invoice_no": "string — invoice or PO number",
    "bill_to": "string — billing customer name and address combined",
    "ship_to": "string — shipping address (if different from bill_to)",
    "terms": "string — payment terms (e.g., 'Due on Receipt', 'Net 30')",
    "items": [
        {{
            "desc": "string — item name/description",
            "details": "string — additional item details (size, color, variant, etc.)",
            "qty": number,
            "unit": "string — unit of measurement (e.g., 'Piece', 'Square feet', 'Kg')",
            "price": number,
            "total": number
        }}
    ],
    "sub_total": number,
    "tax_rate": number,
    "tax_amount": number,
    "grand_total": number
}}
```

### RULES:
1. Return ONLY valid JSON — no markdown, no explanation, no code fences.
2. All numeric fields (qty, price, total, sub_total, tax_rate, tax_amount, grand_total) must be numbers, NOT strings.
3. tax_rate should be a percentage number (e.g., 5.0 for 5%).
4. If a field cannot be found, use null for strings and 0 for numbers.
5. Dates must be converted to YYYY-MM-DD format.
6. Extract ALL line items from the document into the "items" array.
7. The "desc" field should contain the main item name; "details" should have any sub-description (size, color, material, etc.).
8. The "grand_total" should reflect the final total including taxes.

### DOCUMENT TEXT:
\"\"\"
{document_text}
\"\"\"

Respond with the JSON object only:"""


def _clean_json_response(raw: str) -> str:
    """
    Strip markdown code fences and whitespace so we get pure JSON.
    """
    # Remove ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"```", "", cleaned)
    return cleaned.strip()


def _validate_po_data(data: dict) -> dict:
    """
    Validate and coerce the parsed JSON to match the expected schema.
    Ensures numeric fields are actually numbers.
    """
    # Top-level string fields
    string_fields = (
        "vendor_name", "vendor_address", "date", "due_date",
        "invoice_no", "bill_to", "ship_to", "terms",
    )
    for field in string_fields:
        if field not in data or data[field] is None:
            data[field] = "N/A"
        else:
            data[field] = str(data[field])

    # Top-level numeric fields
    for field in ("sub_total", "tax_rate", "tax_amount", "grand_total"):
        try:
            data[field] = float(data.get(field, 0) or 0)
        except (ValueError, TypeError):
            data[field] = 0.0

    # Line items
    raw_items = data.get("items", [])
    if not isinstance(raw_items, list):
        raw_items = []

    validated_items: list[dict] = []
    for item in raw_items:
        validated = {
            "desc": str(item.get("desc", "N/A") or "N/A"),
            "details": str(item.get("details", "") or ""),
            "qty": _safe_number(item.get("qty", 0)),
            "unit": str(item.get("unit", "Piece") or "Piece"),
            "price": _safe_number(item.get("price", 0)),
            "total": _safe_number(item.get("total", 0)),
        }
        validated_items.append(validated)

    data["items"] = validated_items
    return data


def _safe_number(value) -> float:
    """Convert a value to float, defaulting to 0.0 on failure."""
    try:
        return float(value) if value is not None else 0.0
    except (ValueError, TypeError):
        return 0.0


def analyze_purchase_order(text: str, api_key: str) -> dict:
    """
    Send extracted document text to Groq and return structured PO data.

    Uses the groq SDK with Groq().

    Args:
        text: Raw text extracted from the PDF.
        api_key: Groq API key.

    Returns:
        dict matching the PO JSON schema.

    Raises:
        AIAnalysisError: If the API call or JSON parsing fails.
    """
    try:
        logger.info("Initializing Groq client...")
        client = Groq(api_key=api_key)

        prompt = EXTRACTION_PROMPT.format(document_text=text)
        logger.info(f"Sending document to {GROQ_MODEL} for analysis...")

        response = _generate_with_retry(client, prompt)

        if not response.choices or not response.choices[0].message.content:
            raise AIAnalysisError("Groq returned an empty response.")

        raw_text = response.choices[0].message.content
        logger.info(f"Received response — {len(raw_text)} chars.")

        # Parse JSON
        clean_text = _clean_json_response(raw_text)
        try:
            po_data = json.loads(clean_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}\nRaw response:\n{raw_text}")
            raise AIAnalysisError(
                f"Groq's response was not valid JSON. "
                f"Please try again. Parse error: {str(e)}"
            )

        # Validate & coerce types
        validated = _validate_po_data(po_data)
        logger.info("AI analysis complete — data validated successfully.")
        return validated

    except AIAnalysisError:
        raise

    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        error_msg = str(e)
        if "503" in error_msg or "UNAVAILABLE" in error_msg:
            raise AIAnalysisError(
                f"Groq is currently experiencing high demand. "
                f"Please wait a moment and try again. Detailed Error: {error_msg}"
            )
        raise AIAnalysisError(
            f"Failed to communicate with Groq. "
            f"Check your API key and internet connection. Error: {error_msg}"
        )
