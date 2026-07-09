from tools import fee_lookup_tool, document_checklist_tool
from dotenv import load_dotenv
load_dotenv()

# Workaround for CrewAI issue #5886 (cache_breakpoint unsupported by Groq)
import crewai.llms.cache as _crewai_cache
_crewai_cache.mark_cache_breakpoint = lambda msg: msg

from crewai import Agent, Task, Crew, Process, LLM

# --- LLM setup ---
groq_llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    temperature=0.2
)

# --- Sample input scenario (from the assignment) ---
def get_applicant_input():
    """
    Collects applicant details interactively from the user.
    Basic validation included so a bad input doesn't crash the whole crew.
    """
    print("=== Amar Passport AI Agent: Applicant Intake ===\n")

    while True:
        try:
            age = int(input("Enter applicant's age: ").strip())
            break
        except ValueError:
            print("Please enter a valid number for age.")

    profession = input("Enter applicant's profession (e.g. 'private sector employee', "
                        "'government employee', 'student'): ").strip()

    urgency = input("Enter urgency/delivery need (e.g. 'regular', 'need it in 2 weeks', "
                     "'super urgent'): ").strip()

    while True:
        page_preference = input("Page count (48 or 64): ").strip()
        if page_preference in ("48", "64"):
            break
        print("Please enter exactly '48' or '64'.")

    requested_validity = input("Requested passport validity in years (5 or 10): ").strip()

    id_document = input("ID document available (NID / Birth Registration / none): ").strip()

    return {
        "age": age,
        "profession": profession,
        "urgency": urgency,
        "page_preference": page_preference,
        "id_document": id_document,
        "requested_validity": requested_validity
    }


# --- this replaces your old hardcoded dictionary ---
applicant = get_applicant_input()

# ============================================================
# AGENT 1: The Policy Guardian
# ============================================================
policy_guardian = Agent(
    role="Bangladesh Passport Policy Expert",
    goal=(
        "Determine the correct passport validity (5 or 10 years) and the "
        "required identification document (NID or Birth Registration) based "
        "strictly on the applicant's age. Flag any inconsistency between "
        "what the applicant is requesting and what policy actually allows."
    ),
    backstory=(
        "You are a senior official at the Department of Immigration and "
        "Passports (DIP) of Bangladesh with 15 years of experience reviewing "
        "passport eligibility. You are extremely precise about age-based "
        "rules: applicants under 18 may only receive a 5-year validity "
        "passport and must submit Birth Registration (not NID, since minors "
        "often lack one). Applicants over 65 also face specific restrictions "
        "and should be guided toward the appropriate validity. You never let "
        "an incorrect request pass silently -- if a user asks for something "
        "policy does not allow, you clearly flag it and explain the correct "
        "rule instead."
    ),
    llm=groq_llm,
    verbose=True,
    max_iter=5
)

policy_task = Task(
    description=(
        f"Applicant profile: Age = {applicant['age']}, "
        f"Profession = {applicant['profession']}, "
        f"Requested passport validity = {applicant['requested_validity']} years.\n\n"
        "Determine:\n"
        "1. The MAXIMUM/CORRECT validity this applicant is actually eligible for "
        "(5 or 10 years), based strictly on age rules.\n"
        "2. The required identification document type (NID for 18+, Birth "
        "Registration for under 18).\n"
        "3. If the applicant's requested validity does NOT match what policy "
        "allows, explicitly flag this as an INCONSISTENCY and explain why.\n\n"
        "Age rules to apply:\n"
        "- Under 18: only 5-year validity allowed, must use Birth Registration.\n"
        "- 18 to 65: eligible for 5 or 10-year validity, must use NID.\n"
        "- Over 65: eligible for 5 or 10-year validity, must use NID, but "
        "flag that in-person verification may be required.\n"
    ),
    expected_output=(
        "A clear statement with three parts: (1) Eligible Validity, "
        "(2) Required ID Document, (3) Consistency Check result "
        "(state 'No issues found' or describe the flagged inconsistency)."
    ),
    agent=policy_guardian
)



# ============================================================
# AGENT 2: The Chancellor of the Exchequer (Fee Calculator)
# ============================================================
fee_calculator = Agent(
    role="Financial Auditor",
    goal=(
        "Calculate the exact total passport fee in BDT, including 15% VAT, "
        "using the applicant's page count and delivery speed, combined with "
        "the validity period determined by the Policy Guardian."
    ),
    backstory=(
        "You are a meticulous financial auditor for the Department of "
        "Immigration and Passports. You never estimate or guess fees from "
        "memory -- official fee structures change and must always be looked "
        "up using the Fee Lookup Tool. You always cross-check the validity "
        "period against what the Policy Guardian determined, not what the "
        "applicant originally requested, since policy overrides preference."
    ),
    tools=[fee_lookup_tool],
    llm=groq_llm,
    verbose=True,
    max_iter=5
)

fee_task = Task(
    description=(
        f"Using the ELIGIBLE validity period determined by the Policy "
        f"Guardian (not necessarily what the applicant originally requested), "
        f"calculate the total fee.\n\n"
        f"Applicant's page preference: {applicant['page_preference']} pages\n"
        f"Applicant's urgency level: {applicant['urgency']} "
        f"(map this to regular/express/super_express delivery speed)\n\n"
        f"Use the Fee Lookup Tool to get the exact base fee, VAT, and total. "
        f"Do not calculate the VAT yourself -- the tool already does this."
    ),
    expected_output=(
        "A clear statement showing: Page Count, Validity Used, Delivery "
        "Speed, Base Fee, VAT amount, and Total Fee in BDT."
    ),
    agent=fee_calculator,
    context=[policy_task]   # <-- THIS is the task delegation mechanism
)

# ============================================================
# AGENT 3: The Document Architect (Checklist Specialist)
# ============================================================
document_architect = Agent(
    role="Documentation Officer",
    goal=(
        "Determine which applicant category the person falls into (adult, "
        "minor_under_18, or government_staff) and retrieve the exact "
        "required document checklist using the Document Checklist Tool."
    ),
    backstory=(
        "You are a meticulous documentation officer at the Department of "
        "Immigration and Passports. You classify applicants correctly before "
        "looking anything up: government employees need a No Objection "
        "Certificate on top of standard documents, minors need Birth "
        "Registration and parental NID instead of their own NID, and "
        "everyone else follows the standard adult checklist. You always use "
        "the Document Checklist Tool to fetch the official list rather than "
        "guessing from memory."
    ),
    tools=[document_checklist_tool],
    llm=groq_llm,
    verbose=True,
    max_iter=5
)

doc_task = Task(
    description=(
        f"Applicant profile: Age = {applicant['age']}, "
        f"Profession = {applicant['profession']}.\n\n"
        "Using the Policy Guardian's determination of required ID document "
        "type (which tells you if this applicant is a minor or adult), and "
        "the applicant's profession, decide the correct applicant_category "
        "argument to pass to the Document Checklist Tool: "
        "'adult', 'minor_under_18', or 'government_staff'.\n\n"
        "Note: this applicant is a PRIVATE sector employee, not a government "
        "employee, so 'government_staff' does NOT apply here unless the "
        "profession explicitly says government/govt/public sector.\n\n"
        "Call the tool and report the exact document list it returns."
    ),
    expected_output=(
        "A bullet list of required documents for this applicant, with a "
        "one-line explanation of why this category was chosen."
    ),
    agent=document_architect,
    context=[policy_task, fee_task]
)

# ============================================================
# AGENT 4: The Report Compiler (Bilingual Formatter)
# ============================================================
report_compiler = Agent(
    role="Bilingual Report Compiler",
    goal=(
        "Synthesize the Policy Guardian's, Financial Auditor's, and "
        "Documentation Officer's findings into one clean, professional "
        "Passport Readiness Report, presented as a Markdown table, in both "
        "English and Bangla."
    ),
    backstory=(
        "You are a bilingual communications specialist at the Department of "
        "Immigration and Passports, fluent in both English and Bangla. Your "
        "job is not to re-analyze anything -- the eligibility, fee, and "
        "document decisions have already been made by your colleagues. You "
        "simply present their combined findings clearly, accurately, and "
        "without altering any figures or facts, first in English then in "
        "Bangla."
    ),
    llm=groq_llm,
    verbose=True,
    max_iter=5
)

report_task = Task(
    description=(
        "Combine the outputs of the Policy Guardian, Financial Auditor, and "
        "Documentation Officer into a single 'Passport Readiness Report'.\n\n"
        "Output format required:\n"
        "1. An English section with a Markdown table containing these rows: "
        "Validity, Required ID, Delivery Type, Total Fee (BDT), Documents "
        "Needed, and Consistency Check (any flagged issues, or 'No issues found').\n"
        "2. A Bangla section below it with the SAME information translated "
        "into Bangla, also as a Markdown table.\n\n"
        "Do not invent or change any figures -- use exactly what the other "
        "agents determined."
    ),
    expected_output=(
        "A complete bilingual Passport Readiness Report with two Markdown "
        "tables: one in English, one in Bangla, containing identical data."
    ),
    agent=report_compiler,
    context=[policy_task, fee_task, doc_task]
)

# ============================================================
# CREW (just Policy Guardian for now -- we'll add more agents next)
# ============================================================
crew = Crew(
    agents=[policy_guardian, fee_calculator, document_architect, report_compiler],
    tasks=[policy_task, fee_task, doc_task, report_task],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    result = crew.kickoff()
    print("\n\n--- FINAL RESULT ---")
    print(result)