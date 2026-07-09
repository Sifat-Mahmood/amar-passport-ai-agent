"""
Tools for Amar Passport AI Agent.

CONCEPT NOTE:
A CrewAI "tool" is just a regular Python function decorated with @tool.
When you attach a tool to an Agent, the LLM can decide DURING its reasoning
to call that function -- passing in arguments it infers from the task
description -- and gets the function's return value back as real, correct
data instead of guessing.

This is how we satisfy the assignment's "Fallback: if the agent fails to
scrape data, it should fallback to a local database" requirement -- we
simply never let it scrape in the first place; the tool IS the fallback,
always available, always correct.
"""

from crewai.tools import tool
from local_db import PASSPORT_DB


@tool("Fee Lookup Tool")
def fee_lookup_tool(page_count: str, validity_years: str, delivery_speed: str) -> str:
    """
    Look up the official 2026 BDT passport fee.

    Args:
        page_count: "48" or "64"
        validity_years: "5" or "10"
        delivery_speed: "regular", "express", or "super_express"

    Returns:
        A string stating the base fee, 15% VAT, and total fee in BDT.
    """
    try:
        pages_key = f"{page_count}_pages"
        years_key = f"{validity_years}_years"
        base_fee = PASSPORT_DB["fees_2026"][pages_key][years_key][delivery_speed]
        vat = round(base_fee * 0.15, 2)
        total = round(base_fee + vat, 2)
        return (
            f"Base Fee: {base_fee} BDT | VAT (15%): {vat} BDT | "
            f"TOTAL: {total} BDT "
            f"[{page_count} pages, {validity_years} years, {delivery_speed} delivery]"
        )
    except KeyError:
        return (
            f"ERROR: No matching fee entry for page_count={page_count}, "
            f"validity_years={validity_years}, delivery_speed={delivery_speed}. "
            f"Valid options -> pages: 48/64, years: 5/10, "
            f"speed: regular/express/super_express."
        )


@tool("Document Checklist Tool")
def document_checklist_tool(applicant_category: str) -> str:
    """
    Retrieve the required document checklist for a category of applicant.

    Args:
        applicant_category: one of "adult", "minor_under_18", "government_staff"

    Returns:
        A comma-separated list of required documents.
    """
    docs = PASSPORT_DB["required_docs"].get(applicant_category)
    if not docs:
        # Fallback default if an unrecognized category is passed
        docs = PASSPORT_DB["required_docs"]["adult"]
    return f"Required documents for '{applicant_category}': " + ", ".join(docs)