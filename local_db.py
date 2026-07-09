"""
Local fallback database for Amar Passport AI Agent.

Why this exists (concept note for the assignment write-up):
LLMs are prone to "hallucinating" specific numbers (fees, page counts, etc.)
because they generate plausible-sounding text, not verified facts.
Instead of trusting an agent's memory for money-related figures, we store
the ground truth here and expose it to agents through TOOLS (see tools.py).
The agent's job becomes "pick the right lookup and explain it clearly",
not "recall the correct number from training data."
"""

PASSPORT_DB = {
    "fees_2026": {
        "48_pages": {
            "5_years":  {"regular": 4025, "express": 6325,  "super_express": 8625},
            "10_years": {"regular": 5750, "express": 8050,  "super_express": 10350}
        },
        "64_pages": {
            "5_years":  {"regular": 6325, "express": 8625,  "super_express": 12075},
            "10_years": {"regular": 8050, "express": 10350, "super_express": 13800}
        }
    },
    "required_docs": {
        "adult": ["NID Card", "Application Summary", "Payment Slip"],
        "minor_under_18": ["Birth Registration (English)", "Parents NID", "3R Photo"],
        "government_staff": ["NOC (No Objection Certificate)", "NID"]
    }
}