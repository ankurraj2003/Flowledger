"""
=============================================================
Matches extracted item descriptions against an internal SKU
database (simulating a real ERP look-up) using fuzzy string
matching.  Tailored for retail / apparel invoices.
=============================================================
"""

import logging
from difflib import SequenceMatcher

logger = logging.getLogger("flowledger.mapper")

# ─── Placeholder Internal SKU Database ───────────────────────
# In production, this would be a database query or API call.
# Keys   = canonical product descriptions (normalized)
# Values = internal SKU codes
INTERNAL_SKU_DATABASE: dict[str, str] = {
    # ── Apparel — Jeans ──
    "pepe jeans":                           "SKU-APR-PJ-001",
    "pepe jeans tapered fit":               "SKU-APR-PJ-001",
    "pepe jeans mid rise":                  "SKU-APR-PJ-001",
    "levi's jeans":                         "SKU-APR-LV-001",
    "levis jeans":                          "SKU-APR-LV-001",
    "wrangler jeans":                       "SKU-APR-WR-001",
    "denim jeans":                          "SKU-APR-DN-001",
    "slim fit jeans":                       "SKU-APR-SFJ-001",

    # ── Apparel — Shirts ──
    "boys shirt":                           "SKU-APR-BSH-001",
    "boys shirt mosaic":                    "SKU-APR-BSH-001",
    "men shirt":                            "SKU-APR-MSH-001",
    "men shirt mosaic":                     "SKU-APR-MSH-001",
    "casual shirt":                         "SKU-APR-CSH-001",
    "formal shirt":                         "SKU-APR-FSH-001",
    "polo shirt":                           "SKU-APR-PLO-001",
    "t-shirt":                              "SKU-APR-TSH-001",
    "t shirt":                              "SKU-APR-TSH-001",

    # ── Apparel — Trousers / Bottoms ──
    "chinos":                               "SKU-APR-CHN-001",
    "trousers":                             "SKU-APR-TRS-001",
    "cargo pants":                          "SKU-APR-CRG-001",
    "shorts":                               "SKU-APR-SHR-001",
    "track pants":                          "SKU-APR-TRK-001",

    # ── Apparel — Women ──
    "women top":                            "SKU-APR-WTP-001",
    "women blouse":                         "SKU-APR-WBL-001",
    "kurti":                                "SKU-APR-KRT-001",
    "saree":                                "SKU-APR-SAR-001",
    "leggings":                             "SKU-APR-LEG-001",
    "women dress":                          "SKU-APR-WDR-001",

    # ── Apparel — Outerwear ──
    "jacket":                               "SKU-APR-JKT-001",
    "hoodie":                               "SKU-APR-HOD-001",
    "sweater":                              "SKU-APR-SWR-001",
    "blazer":                               "SKU-APR-BLZ-001",

    # ── Accessories ──
    "belt":                                 "SKU-ACC-BLT-001",
    "leather belt":                         "SKU-ACC-BLT-002",
    "wallet":                               "SKU-ACC-WLT-001",
    "cap":                                  "SKU-ACC-CAP-001",
    "scarf":                                "SKU-ACC-SCF-001",
    "tie":                                  "SKU-ACC-TIE-001",
    "socks":                                "SKU-ACC-SOC-001",
    "sunglasses":                           "SKU-ACC-SNG-001",
    "watch":                                "SKU-ACC-WCH-001",
    "handbag":                              "SKU-ACC-HBG-001",

    # ── Footwear ──
    "sneakers":                             "SKU-FTW-SNK-001",
    "loafers":                              "SKU-FTW-LOF-001",
    "sandals":                              "SKU-FTW-SND-001",
    "boots":                                "SKU-FTW-BOT-001",
    "formal shoes":                         "SKU-FTW-FRM-001",
    "sports shoes":                         "SKU-FTW-SPR-001",

    # ── Fabrics / Textiles ──
    "cotton fabric":                        "SKU-FAB-COT-001",
    "silk fabric":                          "SKU-FAB-SLK-001",
    "polyester fabric":                     "SKU-FAB-POL-001",
    "linen fabric":                         "SKU-FAB-LIN-001",
    "denim fabric":                         "SKU-FAB-DNM-001",
    "wool fabric":                          "SKU-FAB-WOL-001",
    "thread spool":                         "SKU-FAB-THR-001",
    "zipper":                               "SKU-FAB-ZIP-001",
    "button set":                           "SKU-FAB-BTN-001",
}

# Matching threshold  (0.0 – 1.0)
MATCH_THRESHOLD = 0.50


def match_sku(description: str) -> str:
    """
    Fuzzy-match a single item description against the internal
    SKU database.

    Args:
        description: Item description from the Invoice / PO.

    Returns:
        Matched SKU code, or "MANUAL REVIEW" if no confident match.
    """
    if not description:
        return "MANUAL REVIEW"

    normalized = description.strip().lower()
    best_score = 0.0
    best_sku = "MANUAL REVIEW"

    for canonical_desc, sku_code in INTERNAL_SKU_DATABASE.items():
        score = SequenceMatcher(None, normalized, canonical_desc).ratio()
        if score > best_score:
            best_score = score
            best_sku = sku_code

    if best_score >= MATCH_THRESHOLD:
        logger.info(f"  ✓ Matched '{description}' → {best_sku} (score: {best_score:.2f})")
        return best_sku
    else:
        logger.warning(
            f"  ⚠ No confident match for '{description}' "
            f"(best score: {best_score:.2f} < {MATCH_THRESHOLD})"
        )
        return "MANUAL REVIEW"


def enrich_items_with_sku(items: list[dict]) -> list[dict]:
    """
    Enrich each line item with an 'internal_sku' field by matching
    its description against the internal SKU database.

    Args:
        items: List of item dicts with at least a 'desc' key.

    Returns:
        Same list with an 'internal_sku' key added to each item.
    """
    logger.info(f"Mapping {len(items)} item(s) to internal SKUs...")
    for item in items:
        item["internal_sku"] = match_sku(item.get("desc", ""))
    matched = sum(1 for i in items if i["internal_sku"] != "MANUAL REVIEW")
    logger.info(f"SKU mapping complete — {matched}/{len(items)} matched automatically.")
    return items
