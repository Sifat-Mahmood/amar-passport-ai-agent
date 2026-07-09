# Amar Passport AI Agent

A Multi-Agent System (MAS) built with **CrewAI** that acts as a "Virtual Consular Officer" for Bangladesh's E-Passport process. Given an applicant's age, profession, and urgency, the system produces a bilingual (English + Bangla) Passport Readiness Report as a Markdown table.
## Demo Video


https://github.com/user-attachments/assets/a3a963c4-0445-46bb-921c-936b9b4a0044



## Overview

Instead of one large prompt trying to handle eligibility rules, fee calculation, and document requirements all at once, this project splits the work across **four specialized agents**, each with a narrow responsibility. This makes the reasoning more reliable, transparent, and easier to debug.

## The Crew

| Agent | Role | Responsibility |
|---|---|---|
| **Policy Guardian** | Bangladesh Passport Policy Expert | Determines eligible validity (5/10 years) and required ID document (NID/Birth Registration) based on age. Flags inconsistencies if the applicant's request violates policy. |
| **Chancellor of the Exchequer** | Financial Auditor | Calculates the exact fee in BDT (including 15% VAT) using a local fee-lookup tool, based on the *eligible* validity determined by the Policy Guardian (not the original request). |
| **Document Architect** | Documentation Officer | Classifies the applicant (adult / minor / government staff) and retrieves the correct document checklist via a local lookup tool. |
| **Report Compiler** | Bilingual Report Compiler | Synthesizes all three agents' outputs into a single Markdown report, in both English and Bangla. |

## Architecture

```
amar-passport-agent/
├── local_db.py     # Fallback source of truth: 2026 fee structure + required docs
├── tools.py         # CrewAI tools that read local_db.py (fee lookup, doc checklist)
├── main.py          # Agent/task/crew definitions, user input, kickoff
├── .env             # GROQ_API_KEY (not committed — see .gitignore)
└── .gitignore
```

### Key design decisions

- **Tools over LLM memory for facts.** Fees and document lists are never "recalled" by the LLM — they're always fetched from `local_db.py` via `@tool`-decorated functions. This satisfies the assignment's fallback requirement: the local database *is* the fallback, always available, never hallucinated.
- **Task delegation via `context=[...]`.** Each downstream task receives the finished output of upstream tasks as part of its own prompt (e.g., the Fee Calculator receives the Policy Guardian's corrected validity). This is how the agents actually collaborate rather than running in isolation.
- **Error handling at two levels:**
  1. Python-level input validation (age must be numeric, page count must be 48/64, etc.)
  2. Agent-level policy validation (e.g., a 15-year-old requesting a 10-year passport gets corrected to 5 years, with the inconsistency explicitly flagged in the final report)

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install crewai crewai-tools litellm python-dotenv
```

Create a `.env` file:
```
GROQ_API_KEY=your_key_here
```

## Running

```bash
python main.py
```

You'll be prompted interactively for the applicant's age, profession, urgency, page preference, requested validity, and available ID document. The crew will then run all four agents sequentially (with `verbose=True` output showing each agent's reasoning and tool calls) and print the final bilingual report.

## Known issue / workaround

Recent versions of CrewAI attach a `cache_breakpoint` field to messages for Anthropic-style prompt caching, which Groq's API rejects. `main.py` includes a small monkey-patch at the top to no-op this behavior:

```python
import crewai.llms.cache as _crewai_cache
_crewai_cache.mark_cache_breakpoint = lambda msg: msg
```

This can be removed once the upstream CrewAI bug is fixed.

## Example scenario (from assignment spec)

**Input:** 24-year-old private sector employee, needs a 64-page passport urgently (business trip in two weeks), has NID.

**Output:** Validity 10 years, Express delivery, Total Fee ≈ 11,902.5 BDT, Documents: NID, Application Summary, Payment Slip.

## Edge case tested

**Input:** 15-year-old requesting a 10-year passport validity.

**Result:** Policy Guardian corrects validity to 5 years, flags the inconsistency, reclassifies required ID as Birth Registration. This correction propagates downstream — the Fee Calculator uses 5 years (not the requested 10) and the Document Architect returns the minor's document checklist (Birth Registration, Parents NID, 3R Photo).
