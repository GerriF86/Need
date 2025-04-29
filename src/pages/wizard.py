import textwrap
import json
import re
import streamlit as st
from pathlib import Path

# ── Cross-cutting components (see cross_components.py) ────────────────
from src.cross_components import (
    ToolRegistry, Guardrails, TraceViewer, DynamicQuestionEngine
)
from src.utils.file_parsers import parse_file      # PDF/DOCX/TXT parser
from src.utils.text_helpers import to_title_case   # normalises job titles

# single ChatGPT handle
chatgpt = ToolRegistry.get_or_register(
    "chatgpt",
    lambda prompt, **kw: ToolRegistry.chatgpt_call(prompt, temperature=0.3, **kw)
)
guard = Guardrails()
trace = TraceViewer()
dq    = DynamicQuestionEngine()     # << keep only this one

# ── Guard patterns ───────────────────────────────────────────────────────
#_URL_RE = re.compile(r"^https?://.+", flags=re.I)
_MAX_FILE_MB = 10
_LANGS = ["German", "English", "Bilingual (DE+EN)"]
_TONES = ["Casual", "Neutral", "Formal", "Enthusiastic"]
_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
_TEL_RE   = re.compile(r"^[0-9\+\-\s]{6,}$")
_SALARY_RE = re.compile(r"\s*(\d[\d\.]*)\s*[-–]\s*(\d[\d\.]*)\s*$")   # 50 000 – 65 000
FIELDS_MUST = ["mustHaveSkills", "hardSkills"]
FIELDS_NICE = ["niceToHaveSkills", "softSkills"]
FIELDS_EXTRA = [
    ("languageRequirements",   "Language Requirements (e.g. EN C1, DE B2)"),
    ("toolProficiency",        "Tool Proficiency (comma-list)"),
    ("technicalStack",         "Technical Stack"),
    ("domainExpertise",        "Domain Expertise"),
    ("leadershipCompetencies", "Leadership Competencies"),
    ("certificationsRequired", "Certifications Required"),
    ("industryExperience",     "Years of Industry Experience"),
    ("analyticalSkills",       "Analytical Skills"),
    ("communicationSkills",    "Communication Skills"),
    ("projectManagementSkills","Project-Management Skills"),
    ("softRequirementDetails", "Other Soft Requirements"),
    ("visaSponsorship",        "Visa Sponsorship Needed? (Yes / No / Case-by-Case)")
]
CURRENCIES  = ["EUR", "USD", "GBP", "CHF"]
FREQUENCIES = ["Annual", "Monthly", "Bi-Weekly", "Weekly"]
CATS = [
    ("taskList",               "General Task List"),
    ("keyResponsibilities",    "Key Responsibilities (3-5 bullets)"),
    ("technicalTasks",         "Technical Tasks"),
    ("managerialTasks",        "Managerial Tasks"),
    ("administrativeTasks",    "Administrative / Reporting Tasks"),
    ("customerFacingTasks",    "Customer-Facing Tasks"),
    ("internalReportingTasks", "Internal Reporting Tasks"),
    ("performanceTasks",       "Performance-Related Tasks"),
    ("innovationTasks",        "Innovation / R&D Tasks"),
]
_ROLE_TYPES = ["Individual Contributor", "Team Lead", "Manager",
               "Director", "Executive / C-Level", "Other"]

def discovery_page():
    st.header("Step 1 · Discovery 📥")
    st.write(
        "Provide **at least** a job title. Optionally paste a URL to an existing job "
        "ad or upload a PDF/DOCX/TXT. Vacalyser will extract as much information as "
        "possible to speed-up the next steps."
    )

    # ── 1 · Job Title ────────────────────────────────────────────────────
    job_title_in = st.text_input("Job Title*", key="jobTitle")
    if job_title_in:
        st.session_state["jobTitle"] = to_title_case(job_title_in.strip())

    # ── 2 · Source URL ───────────────────────────────────────────────────
    url_in = st.text_input("Ad / Company URL", key="inputUrl", placeholder="https://…")
    if url_in and not _URL_RE.match(url_in):
        st.warning("URL must start with http(s)://")
    st.session_state["inputUrl"] = url_in.strip()

    # ── 3 · File Upload ──────────────────────────────────────────────────
    file = st.file_uploader("Upload Job Ad (PDF · DOCX · TXT, ≤ 10 MB)", type=["pdf", "docx", "txt"])
    if file:
        if file.size > _MAX_FILE_MB * 1024 * 1024:
            st.error(f"File larger than {_MAX_FILE_MB} MB.")
            file = None
        else:
            st.session_state["uploadedFile"] = file

    # ── 4 · Analyse Sources Button ───────────────────────────────────────
    if st.button("Analyse Sources"):
        raw_text = ""

        # — Fetch from URL if present —
        if st.session_state["inputUrl"]:
            # Only ChatGPT allowed ⇒ let it fetch page text via its knowledge
            prompt = (
                "You are an extraction agent. Retrieve **visible text** from this URL "
                "and return it as plain UTF-8 text (no HTML, no markdown).\nURL: "
                f"{st.session_state['inputUrl']}\n"
            )
            raw_text = chatgpt(prompt, max_tokens=2048)

        # — If file uploaded, parse it (overrides URL text if both) —
        if file:
            raw_text = parse_file(file, file.name)

        if not raw_text:
            st.error("Nothing to analyse – please provide a valid URL or file.")
            return

        # Save raw text
        st.session_state["parsedDataRaw"] = raw_text
        trace.log("parse_complete", size=len(raw_text))

        # — Quick language detect (ChatGPT) —
        lang = chatgpt(
            "Detect the language (ISO-639-1 code) of the following text. Respond with "
            "only the code, nothing else:\n\n" + raw_text[:400]
        )
        st.session_state["sourceLanguage"] = lang.lower()

        # — Extract entities (company name, salary flag) —
        extraction_prompt = (
            "Extract the following from the text below. Return JSON **only** with keys "
            "`detectedCompanyName` and `competitiveSalaryFlag` (true/false). "
            "competitiveSalaryFlag = true if phrases like 'competitive salary' or "
            "'marktübliches Gehalt' are present.\n\nTEXT:\n```"
            + raw_text[:4000] + "```"
        )
        extraction_json = chatgpt(extraction_prompt, max_tokens=300)
        try:
            data = guard.json_or_raise(extraction_json, {"detectedCompanyName": str, "competitiveSalaryFlag": bool})
            st.session_state.update(data)
        except ValueError:
            trace.log("extraction_failed", details=extraction_json)
            st.warning("Could not reliably extract company or salary info.")

        # — Dynamic follow-ups —
        if st.session_state.get("competitiveSalaryFlag"):
            dq.enqueue(
                "salary_range",
                "You wrote ‘competitive salary’. What salary range (min–max) do you "
                "have in mind?"
            )

        # — Preview —
        with st.expander("Parsed Preview (first 600 chars)"):
            st.write(st.session_state["parsedDataRaw"][:600] + "…")

        st.success("Source analysis complete!")

    # ── 5 · Pending Dynamic Questions ────────────────────────────────────
    dq.render_pending_questions()

    # ── 6 · Trace Viewer (collapsible) ───────────────────────────────────
    with st.expander("Trace Log"):
        trace.render_ui()
def job_company_page():
    st.header("Step 2 · Job & Company 🏢")
    st.caption("Fill in company basics and job-level info. Fields marked * are required.")

    # ── Group: Company Basics ────────────────────────────────────────────
    with st.form("company_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state["companyName"] = st.text_input("Company Name*", value=st.session_state.get("companyName", ""))
            st.session_state["brandName"]   = st.text_input("Brand / Product Line", value=st.session_state.get("brandName", ""))
            st.session_state["headquartersLocation"] = st.text_input("HQ Location", value=st.session_state.get("headquartersLocation", ""))
            st.session_state["city"] = st.text_input("City (Job Location)", value=st.session_state.get("city", ""))

        with col2:
            website = st.text_input("Company Website", value=st.session_state.get("companyWebsite", ""))
            if website and not _URL_RE.match(website):
                st.warning("Please enter a valid https:// URL")
            st.session_state["companyWebsite"] = website
            st.session_state["companySize"] = st.selectbox("Company Size (head-count)", ["", "<50", "50-249", "250-999", "1000-4999", "5000+"], index=0, key="companySize")
            st.session_state["industrySector"] = st.text_input("Industry Sector", value=st.session_state.get("industrySector", ""))

        st.divider()

        # ── Group: Job Basics ────────────────────────────────────────────
        col3, col4 = st.columns(2)
        with col3:
            st.session_state["jobType"]   = st.selectbox("Job Type*", ["Full-Time", "Part-Time", "Internship", "Freelance", "Volunteer", "Other"], key="jobType")
            st.session_state["contractType"] = st.selectbox("Contract Type*", ["Permanent", "Fixed-Term", "Contractor/Freelance", "Other"], key="contractType")
            st.session_state["jobLevel"]  = st.selectbox("Job Level*", ["Entry", "Mid", "Senior", "Director", "C-Level"], key="jobLevel")
        with col4:
            st.session_state["teamStructure"] = st.text_area("Team Structure (optional)", value=st.session_state.get("teamStructure", ""), height=90)
            st.session_state["dateOfEmploymentStart"] = st.text_input("Preferred Start Date (e.g. ASAP or 2025-06-01)", value=st.session_state.get("dateOfEmploymentStart", ""))

        submitted = st.form_submit_button("Save & Enrich 🚀")
    # end form

    # ── 1  ·  Guardrail validation & trace  ─────────────────────────────
    if submitted:
        # Required checks
        missing = [k for k in ("companyName", "jobType", "contractType", "jobLevel") if not st.session_state.get(k)]
        if missing:
            st.error(f"Missing required fields: {', '.join(missing)}")
            return

        trace.log("step2_saved", keys_filled=[k for k in st.session_state.keys() if st.session_state[k]])

        # ── 2  ·  Enrichment via ChatGPT  (companySize / industrySector) ─
        if not st.session_state.get("companySize") or not st.session_state.get("industrySector"):
            enrich_prompt = (
                "You are a business knowledge assistant. For the German labour market, "
                "return JSON with keys `guessSize` (one of '<50','50-249','250-999','1000-4999','5000+') "
                "and `sector` (1-3 word industry) for company «{name}». "
                "If unsure, use empty string.\n\nCompany: {name}"
            ).format(name=st.session_state["companyName"])
            resp = chatgpt(enrich_prompt, max_tokens=120)
            try:
                data = guard.json_or_raise(resp, {"guessSize": str, "sector": str})
                if not st.session_state.get("companySize"):
                    st.session_state["companySize"] = data["guessSize"]
                if not st.session_state.get("industrySector"):
                    st.session_state["industrySector"] = data["sector"]
                trace.log("company_enriched", source="chatgpt", data=data)
            except ValueError:
                trace.log("enrichment_failed", resp=resp)

        # ── 3  ·  Dynamic follow-ups (examples) ──────────────────────────
        if st.session_state["contractType"] == "Fixed-Term" and not st.session_state.get("legalDisclaimers"):
            dq.enqueue(
                "legal_disclaimers",
                "You selected a fixed-term contract. Please provide the legal reason for limitation "
                "§14 TzBfG (e.g. project, maternity cover)."
            )
        if not st.session_state.get("probationPeriodMonths"):
            dq.enqueue(
                "probationPeriodMonths",
                "What will be the probation period (in months)? Typical in Germany is 6."
            )

        st.success("Data saved ✔. You can tweak fields or move to the next step.")

    # ── 4  ·  Pending dynamic questions  ────────────────────────────────
    dq.render_pending_questions()

    # ── 5  ·  Trace viewer (collapsible)  ───────────────────────────────
    with st.expander("Trace Log"):
        trace.render_ui()

def role_definition_page() -> None:
    st.header("Step 3 · Role Definition 🎯")

    # ── 1 · Main Form ────────────────────────────────────────────────────
    with st.form("role_form"):
        st.subheader("Role Summary")
        st.session_state["roleDescription"] = st.text_area(
            "Role Description* (max ~120 words)",
            value=st.session_state.get("roleDescription", ""),
            height=120,
            key="roleDescription"
        )
        st.session_state["roleType"] = st.selectbox(
            "Role Type*", _ROLE_TYPES, key="roleType",
            index=_ROLE_TYPES.index(st.session_state.get("roleType", _ROLE_TYPES[0]))
        )
        col1, col2 = st.columns(2)
        with col1:
            st.session_state["reportsTo"] = st.text_input(
                "Reports To",
                value=st.session_state.get("reportsTo", "")
            )
            st.session_state["rolePerformanceMetrics"] = st.text_area(
                "Performance Metrics (KPIs)",
                value=st.session_state.get("rolePerformanceMetrics", ""),
                height=90
            )
            st.session_state["decisionMakingAuthority"] = st.text_input(
                "Decision-Making Authority (e.g. budget €)",
                value=st.session_state.get("decisionMakingAuthority", "")
            )
        with col2:
            st.session_state["supervises"] = st.text_input(
                "Direct Reports (head-count)",
                value=st.session_state.get("supervises", "")
            )
            st.session_state["rolePriorityProjects"] = st.text_area(
                "Priority Projects",
                value=st.session_state.get("rolePriorityProjects", ""),
                height=90
            )
            st.session_state["budgetResponsibility"] = st.text_input(
                "Budget Responsibility (optional)",
                value=st.session_state.get("budgetResponsibility", "")
            )

        st.divider()
        st.subheader("Logistics")
        col3, col4 = st.columns(2)
        with col3:
            st.session_state["travelRequirements"] = st.text_input(
                "Travel Requirements (e.g. ‘up to 20 %’)",
                value=st.session_state.get("travelRequirements", "")
            )
            st.session_state["workModePercentRemote"] = st.slider(
                "Remote Work % of Time", 0, 100,
                value=int(st.session_state.get("workModePercentRemote", 0)),
                step=10
            )
        with col4:
            st.session_state["workSchedule"] = st.text_input(
                "Work Schedule (e.g. 9-5, shifts)",
                value=st.session_state.get("workSchedule", "")
            )
            st.session_state["roleKeywords"] = st.text_input(
                "Role Keywords (comma-separated)",
                value=st.session_state.get("roleKeywords", "")
            )

        saved = st.form_submit_button("Save & Enrich 🚀")
    # end form

    # ── 2 · Validation & Auto-helpers ───────────────────────────────────
    if saved:
        if not st.session_state["roleDescription"].strip():
            st.error("Role description is required.")
            return

        trace.log("step3_saved")

        # Summarise role description to 120 words if longer
        if len(st.session_state["roleDescription"].split()) > 120:
            summarise_prompt = (
                "Summarise the following role description into **at most 120 words**, "
                "keep German if source text is German, otherwise English.\n\n### TEXT\n"
                f"{st.session_state['roleDescription']}"
            )
            summary = chatgpt(summarise_prompt, max_tokens=180)
            if summary:
                st.session_state["roleDescription"] = summary.strip()
                st.info("Description auto-shortened to ≈120 words.")
                trace.log("description_shortened")

        # Dynamic questions
        if (st.session_state["roleType"] in {"Manager", "Director", "Executive / C-Level"}
                and not st.session_state["leadershipCompetencies"]):
            dq.enqueue(
                "leadership_competencies",
                "Because this is a leadership role, please list 2-3 key leadership "
                "competencies (e.g. ‘Coaching’, ‘Strategic Thinking’)."
            )

        if (st.session_state["travelRequirements"].strip()
                and "50" in st.session_state["travelRequirements"]):
            dq.enqueue(
                "relocation_assistance",
                "Travel requirement is high (>50 %). Should we offer relocation "
                "assistance or BahnCard allowance?"
            )

        st.success("Role data saved ✔")

    # ── 3 · Pending dynamic questions ───────────────────────────────────
    dq.render_pending_questions()

    # ── 4 · Trace viewer ────────────────────────────────────────────────
    with st.expander("Trace Log"):
        trace.render_ui()

def tasks_page() -> None:
    st.header("Step 4 · Tasks & Responsibilities 🗂️")
    st.write("List the tasks the role performs. Vacalyser can auto-classify and "
             "calculate task complexity for salary benchmarking.")

    # ── 1 · Task Inputs (one big form) ───────────────────────────────────
    with st.form("tasks_form"):
        for key, label in CATS:
            st.session_state[key] = st.text_area(
                label,
                value=st.session_state.get(key, ""),
                height=100 if key == "taskList" else 70
            )
        st.session_state["taskPrioritization"] = st.text_area(
            "Task Prioritization (optional, e.g. MoSCoW ranking)",
            value=st.session_state.get("taskPrioritization", ""),
            height=60
        )
        saved = st.form_submit_button("Save & Classify 🚀")
    # end form

    # ── 2 · Auto-classification & complexity score ──────────────────────
    if saved:
        # Basic presence check
        if not st.session_state["taskList"].strip():
            st.error("Please provide at least a general task list.")
            return

        trace.log("step4_saved")

        # Build one prompt for all tasks
        full_tasks = "\n".join(
            f"## {label}\n{st.session_state[key]}"
            for key, label in CATS if st.session_state[key].strip()
        )

        classify_prompt = (
            "You are an HR assistant. For the German tech market classify the tasks "
            "into Technical, Managerial, Administrative, Customer-Facing, Innovation. "
            "Return JSON with keys:\n"
            "  categories: {tech:int, managerial:int, admin:int, customer:int, innov:int}\n"
            "  complexityScore: float 0-1 (0=trivial, 1=highly complex)\n\n"
            "TASKS:\n"
            f"{full_tasks}"
        )
        raw_json = chatgpt(classify_prompt, max_tokens=200)
        try:
            schema = {
                "categories": dict,
                "complexityScore": (float, int)
            }
            data = guard.json_or_raise(raw_json, schema)
            st.session_state["taskComplexityScore"] = float(data["complexityScore"])
            trace.log("tasks_classified", data=data)
            st.success("Tasks classified ✅")

            # Dynamic salary bump question if complexity high
            if st.session_state["taskComplexityScore"] >= 0.7:
                dq.enqueue(
                    "salary_range",
                    "These tasks are highly complex. Would you like to raise the "
                    "salary range accordingly?"
                )

        except ValueError:
            trace.log("classification_failed", raw=raw_json)
            st.warning("Could not parse classification – consider refining bullets.")

    # ── 3 · Pending dynamic questions ───────────────────────────────────
    dq.render_pending_questions()

    # ── 4 · Trace viewer ────────────────────────────────────────────────
    with st.expander("Trace Log"):
        trace.render_ui()

def skills_page():
    st.header("Step 5 · Skills & Competencies 🛠️")

    with st.form("skills_form"):
        st.subheader("Must-Have Skills")
        for key in FIELDS_MUST:
            st.session_state[key] = st.text_area(
                key.replace("Skills", " Skills"), value=st.session_state.get(key, ""), height=90
            )

        st.subheader("Nice-to-Have Skills")
        for key in FIELDS_NICE:
            st.session_state[key] = st.text_area(
                key.replace("Skills", " Skills"), value=st.session_state.get(key, ""), height=70
            )

        st.divider(); st.subheader("Additional Details")
        for key, label in FIELDS_EXTRA:
            st.session_state[key] = st.text_input(label, value=st.session_state.get(key, ""))

        submitted = st.form_submit_button("Save & Analyse 🚀")

    # ── 1 · Validation ──────────────────────────────────────────────────
    if submitted:
        if not st.session_state["mustHaveSkills"].strip():
            st.error("Please provide at least one must-have skill.")
            return

        trace.log("step5_saved")

        # ── 2 · ChatGPT rarity & gap analysis ───────────────────────────
        skills_prompt = (
            "For the German labour market, analyse the following skills. "
            "Return JSON with:\n"
            "  skillRarityIndex: float 0-1 (higher = rarer),\n"
            "  skillGapScore: float 0-1 (higher = big gap between must & nice-to-have)\n"
            "DO NOT add extra keys.\n\n"
            f"MUST: {st.session_state['mustHaveSkills']}\n"
            f"NICE: {st.session_state['niceToHaveSkills']}"
        )
        raw_json = chatgpt(skills_prompt, max_tokens=120)
        try:
            data = guard.json_or_raise(raw_json, {
                "skillRarityIndex": (float, int),
                "skillGapScore":   (float, int)
            })
            st.session_state["skillRarityIndex"] = float(data["skillRarityIndex"])
            st.session_state["skillGapScore"]    = float(data["skillGapScore"])
            trace.log("skills_analyzed", data=data)
            st.success("Skill rarity & gap analysed ✅")

            # ── Dynamic questions based on results ──────────────────
            if st.session_state["skillRarityIndex"] >= 0.7:
                dq.enqueue(
                    "salary_range",
                    "Rare skills detected. Do you want to adjust the salary range upward?"
                )
            if (st.session_state.get("visaSponsorship","").lower().startswith("yes") and
                    st.session_state["skillGapScore"] >= 0.5):
                dq.enqueue(
                    "recruitment_timeline",
                    "Visa sponsorship and skill gap suggest a longer hiring timeline. "
                    "How many weeks should we plan?"
                )

        except ValueError:
            trace.log("analysis_failed", raw=raw_json)
            st.warning("Could not parse rarity analysis – please refine skills.")

    # ── 3 · Pending dynamic questions ───────────────────────────────────
    dq.render_pending_questions()

    # ── 4 · Trace viewer ────────────────────────────────────────────────
    with st.expander("Trace Log"):
        trace.render_ui()

def compensation_page() -> None:
    st.header("Step 6 · Compensation & Benefits 💶")

    with st.form("comp_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state["salaryRange"] = st.text_input(
                "Salary Range (min – max, numbers only)*",
                value=st.session_state.get("salaryRange", "")
            )
            st.session_state["currency"] = st.selectbox(
                "Currency*", CURRENCIES,
                index=CURRENCIES.index(st.session_state.get("currency", "EUR"))
            )
            st.session_state["payFrequency"] = st.selectbox(
                "Pay Frequency*", FREQUENCIES,
                index=FREQUENCIES.index(st.session_state.get("payFrequency", "Annual"))
            )
            st.session_state["bonusScheme"] = st.text_input(
                "Bonus Scheme",
                value=st.session_state.get("bonusScheme", "")
            )
            st.session_state["commissionStructure"] = st.text_input(
                "Commission Structure",
                value=st.session_state.get("commissionStructure", "")
            )
        with col2:
            st.session_state["vacationDays"] = st.number_input(
                "Vacation Days", 20, 40,
                value=int(st.session_state.get("vacationDays") or 28)
            )
            st.session_state["remoteWorkPolicy"] = st.selectbox(
                "Remote Work Policy", ["On-site", "Hybrid", "Full Remote", "Other"],
                index=["On-site","Hybrid","Full Remote","Other"].index(
                    st.session_state.get("remoteWorkPolicy","On-site")
                )
            )
            st.session_state["flexibleHours"] = st.selectbox(
                "Flexible Hours", ["No", "Yes", "Partial / Core-time"],
                index=["No","Yes","Partial / Core-time"].index(
                    st.session_state.get("flexibleHours","No")
                )
            )
            st.session_state["relocationAssistance"] = st.selectbox(
                "Relocation Assistance", ["None", "Allowance", "Full Package", "Case-by-Case"],
                index=["None","Allowance","Full Package","Case-by-Case"].index(
                    st.session_state.get("relocationAssistance","None")
                )
            )
            st.session_state["childcareSupport"] = st.selectbox(
                "Childcare Support", ["No", "Yes", "Subsidy"],
                index=["No","Yes","Subsidy"].index(
                    st.session_state.get("childcareSupport","No")
                )
            )

        st.divider()
        st.session_state["bahnCardAllowance"] = st.checkbox(
            "Offer BahnCard / travel allowance", value=st.session_state.get("bahnCardAllowance", False)
        )
        st.session_state["jobRadOption"]     = st.checkbox(
            "Offer JobRad / bike-leasing", value=st.session_state.get("jobRadOption", False)
        )
        st.session_state["collectiveAgreement"] = st.checkbox(
            "Subject to Collective Agreement (Tarifvertrag)",
            value=st.session_state.get("collectiveAgreement", False)
        )

        saved = st.form_submit_button("Save & Benchmark 🚀")
    # end form

    # ── 1 · Guardrail validation ────────────────────────────────────────
    if saved:
        m = _SALARY_RE.match(st.session_state["salaryRange"])
        if not m:
            st.error("Salary Range must look like 50000 – 65000")
            return
        low, high = map(lambda x: float(x.replace(".","")), m.groups())
        if low >= high:
            st.error("Min salary must be lower than max salary.")
            return

        trace.log("step6_saved")

        # ── 2 · Market benchmark via ChatGPT ────────────────────────────
        bench_prompt = (
            "For the German labour market, estimate a fair annual salary range "
            "in {currency} for a «{jobTitle}» in {city}. "
            "Respond with JSON {{benchLow: number, benchHigh: number}} only."
        ).format(
            currency=st.session_state["currency"],
            jobTitle=st.session_state.get("jobTitle","(title unknown)"),
            city=st.session_state.get("city","Germany")
        )
        resp = chatgpt(bench_prompt, max_tokens=60)
        try:
            bench = guard.json_or_raise(resp, {"benchLow": (float,int), "benchHigh": (float,int)})
            st.session_state["salaryBenchmarkLocal"] = (bench["benchLow"], bench["benchHigh"])
            trace.log("salary_benchmark", data=bench)

            # Δ check
            delta_low  = (low  - bench["benchLow"])  / bench["benchLow"]
            delta_high = (high - bench["benchHigh"]) / bench["benchHigh"]
            if abs(delta_low) > 0.15 or abs(delta_high) > 0.15:
                st.warning(
                    f"Entered salary differs ≥15 % from local benchmark "
                    f"({bench['benchLow']}–{bench['benchHigh']} {st.session_state['currency']})."
                )
                dq.enqueue(
                    "salary_range",
                    "Salary range appears misaligned with market data. Adjust?"
                )
        except ValueError:
            trace.log("benchmark_failed", raw=resp)

        # ── 3 · Relocation advisory (geoDistance set by earlier step) ───
        geo_km = st.session_state.get("geoDistance")
        if geo_km and geo_km >= 100 and st.session_state["relocationAssistance"] == "None":
            dq.enqueue(
                "relocation_assistance",
                f"The candidate may need to relocate ({geo_km} km). "
                "Should we add relocation assistance?"
            )

        # ── 4 · Collective Agreement guardrail ──────────────────────────
        if st.session_state["collectiveAgreement"] and low < 30000:
            dq.enqueue(
                "salary_range",
                "Collective Agreement detected: the minimum salary may be too low. "
                "Please confirm or adjust."
            )

        st.success("Compensation data saved ✔")

    # ── 5 · Dynamic questions ───────────────────────────────────────────
    dq.render_pending_questions()

    # ── 6 · Trace viewer ────────────────────────────────────────────────
    with st.expander("Trace Log"):
        trace.render_ui()

def recruitment_page():
    st.header("Step 7 · Recruitment Process 🗂️")

    with st.form("recruit_form"):
        st.subheader("Candidate Journey")
        st.session_state["recruitmentSteps"] = st.text_area(
            "Recruitment Steps (bullet list)*",
            value=st.session_state.get("recruitmentSteps",""),
            height=100
        )
        col1, col2 = st.columns(2)
        with col1:
            st.session_state["numberOfInterviews"] = st.number_input(
                "Number of Interview Rounds", 1, 10,
                value=int(st.session_state.get("numberOfInterviews") or 2)
            )
            st.session_state["interviewFormat"] = st.selectbox(
                "Main Interview Format",
                ["On-site", "Video", "Phone", "Hybrid"],
                index=["On-site","Video","Phone","Hybrid"].index(
                    st.session_state.get("interviewFormat","On-site"))
            )
            st.session_state["assessmentTests"] = st.text_area(
                "Assessment Tests (if any)",
                value=st.session_state.get("assessmentTests",""),
                height=70
            )
        with col2:
            st.session_state["recruitmentTimeline"] = st.text_input(
                "Target Timeline (weeks)",
                value=st.session_state.get("recruitmentTimeline","4")
            )
            st.session_state["onboardingProcessOverview"] = st.text_area(
                "Onboarding Process Overview",
                value=st.session_state.get("onboardingProcessOverview",""),
                height=70
            )
            st.session_state["probationPeriodMonths"] = st.number_input(
                "Probation Period (months)",
                0, 12, value=int(st.session_state.get("probationPeriodMonths") or 6)
            )

        st.divider(); st.subheader("Contacts & Instructions")
        col3, col4 = st.columns(2)
        with col3:
            st.session_state["recruitmentContactEmail"] = st.text_input(
                "Recruitment Contact Email*",
                value=st.session_state.get("recruitmentContactEmail","")
            )
            st.session_state["recruitmentContactPhone"] = st.text_input(
                "Contact Phone (optional)",
                value=st.session_state.get("recruitmentContactPhone","")
            )
        with col4:
            st.session_state["applicationInstructions"] = st.text_area(
                "Application Instructions",
                value=st.session_state.get("applicationInstructions",""),
                height=90
            )
            st.session_state["worksCouncilInvolved"] = st.checkbox(
                "Works Council (Betriebsrat) must approve hires",
                value=st.session_state.get("worksCouncilInvolved", False)
            )

        saved = st.form_submit_button("Save & Generate 🚀")
    # end form

    # ── 1 · Validation ───────────────────────────────────────────────────
    if saved:
        if not st.session_state["recruitmentSteps"].strip():
            st.error("Recruitment steps are required.")
            return
        mail = st.session_state["recruitmentContactEmail"].strip()
        if not _EMAIL_RE.match(mail):
            st.error("Please enter a valid email address.")
            return
        phone = st.session_state["recruitmentContactPhone"].strip()
        if phone and not _TEL_RE.match(phone):
            st.error("Phone number seems invalid.")
            return

        trace.log("step7_saved")

        # ── 2 · Interview Questions (ChatGPT) ────────────────────────────
        if not st.session_state.get("interviewQuestions"):
            iq_prompt = (
                "Generate 6 structured interview questions for a «{title}» role, "
                "covering must-have & soft skills:\n"
                "MUST: {must}\nSOFT: {soft}"
            ).format(
                title=st.session_state.get("jobTitle", "unknown"),
                must = st.session_state.get("mustHaveSkills",""),
                soft = st.session_state.get("softSkills","")
            )
            iq_text = chatgpt(iq_prompt, max_tokens=300)
            st.session_state["interviewQuestions"] = iq_text.strip()
            trace.log("interview_questions_generated")

        # ── 3 · Boolean Query for DACH job boards ────────────────────────
        if not st.session_state.get("booleanQueryDachJobboards"):
            bq_prompt = (
                "Create a single-line Boolean search string (AND/OR) in German for "
                "LinkedIn Recruiter to find candidates for: {title}. "
                "Must-have skills: {skills}. City: {city or 'Germany'}."
            ).format(
                title = st.session_state.get("jobTitle",""),
                skills= st.session_state.get("mustHaveSkills","").replace("\n",", "),
                city  = st.session_state.get("city")
            )
            bq = chatgpt(bq_prompt, max_tokens=120)
            st.session_state["booleanQueryDachJobboards"] = bq.strip()
            trace.log("boolean_query_generated")

        # ── 4 · Dynamic Qs based on rounds & works council ───────────────
        rounds = st.session_state["numberOfInterviews"]
        if rounds > 4:
            dq.enqueue(
                "number_of_interviews",
                "You have more than 4 interview rounds. Consider merging or dropping one. "
                "Would you like to reduce the number?"
            )
        if st.session_state["worksCouncilInvolved"]:
            dq.enqueue(
                "recruitment_timeline",
                "Works Council approval may extend the timeline. Adjust weeks?"
            )

        st.success("Recruitment data saved ✔")

    # ── 5 · Dynamic questions queue ─────────────────────────────────────
    dq.render_pending_questions()

    # ── 6 · Trace viewer ────────────────────────────────────────────────
    with st.expander("Trace Log"):
        trace.render_ui()

def summary_page() -> None:
    st.header("Step 8 · Additional & Summary 📑")

    # ── 1 · Form inputs ─────────────────────────────────────────────────
    with st.form("summary_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.session_state["adSeniorityTone"] = st.selectbox(
                "Ad Tone*", _TONES,
                index=_TONES.index(st.session_state.get("adSeniorityTone", "Neutral"))
            )
            st.session_state["adLengthPreference"] = st.selectbox(
                "Ad Length Preference*", ["Short", "Standard", "Detailed"],
                index=["Short","Standard","Detailed"].index(
                    st.session_state.get("adLengthPreference","Standard")
                )
            )
            st.session_state["languageOfAd"] = st.selectbox(
                "Language of Ad*", _LANGS,
                index=_LANGS.index(st.session_state.get("languageOfAd","German"))
            )
            st.session_state["translationRequired"] = st.checkbox(
                "Need automatic translation",
                value=st.session_state.get("translationRequired", False)
            )
            st.session_state["desiredPublicationChannels"] = st.text_input(
                "Publication Channels (comma-list)",
                value=st.session_state.get("desiredPublicationChannels", "")
            )
            st.session_state["deadlineUrgency"] = st.text_input(
                "Application Deadline / Urgency (e.g. ‘ASAP’ or ‘2025-05-31’)",
                value=st.session_state.get("deadlineUrgency", "")
            )
        with col2:
            st.session_state["employerBrandingElements"] = st.text_area(
                "Branding Elements (links / slogans)",
                value=st.session_state.get("employerBrandingElements", ""),
                height=80
            )
            st.session_state["diversityInclusionStatement"] = st.text_area(
                "D&I Statement (≤ 100 words)",
                value=st.session_state.get("diversityInclusionStatement", ""),
                height=80
            )
            st.session_state["legalDisclaimers"] = st.text_area(
                "Legal Disclaimers",
                value=st.session_state.get("legalDisclaimers", ""),
                height=60
            )
            st.session_state["companyAwards"] = st.text_input(
                "Company Awards / PR Highlights",
                value=st.session_state.get("companyAwards", "")
            )
            st.session_state["videoIntroductionOption"] = st.selectbox(
                "Video Intro available?",
                ["No","Yes"],
                index=["No","Yes"].index(st.session_state.get("videoIntroductionOption","No"))
            )
        st.divider()
        st.subheader("Internal")
        st.session_state["commentsInternal"] = st.text_area(
            "Internal Comments (never published)",
            value=st.session_state.get("commentsInternal", ""), height=80
        )
        saved = st.form_submit_button("Generate Summary 🚀")
    # end form

    # ── 2 · Validation & Guardrails ─────────────────────────────────────
    if saved:
        words_di = len(st.session_state["diversityInclusionStatement"].split())
        if words_di > 100:
            st.warning("D&I statement is longer than 100 words.")
            return
        trace.log("step8_saved")

        # ── SEO keyword generation if missing ───────────────────────────
        if not st.session_state.get("seoKeywords"):
            kw_prompt = (
                "Suggest ten SEO keywords (comma-separated, no #) for a job ad titled "
                "«{title}» in {city}. Return one comma-list only."
            ).format(
                title=st.session_state.get("jobTitle",""),
                city =st.session_state.get("city","Germany")
            )
            kw_line = chatgpt(kw_prompt, max_tokens=60)
            st.session_state["seoKeywords"] = kw_line.strip()
            trace.log("seo_keywords_generated")

        # ── Job-Ad Generation (DE & EN) ─────────────────────────────────
        ad_prompt = textwrap.dedent("""
            Compose a {length} {tone} job advertisement in {lang}. 
            Use markdown bullets for tasks and skills.
            Insert the diversity statement at the end.

            ### Inputs
            Job Title: {title}
            Company: {company}
            City: {city}
            Role Description: {descr}
            Key Tasks: {tasks}
            Must-Have Skills: {must}
            Nice-To-Have: {nice}
            Compensation: {salary}
            Perks: {vacation} days vacation, {flexHours} flex hours, {remote} remote policy
            Publication Channels: {channels}
            """).format(
                length = st.session_state["adLengthPreference"].lower(),
                tone   = st.session_state["adSeniorityTone"].lower(),
                lang   = "German" if st.session_state["languageOfAd"].startswith("German") else "English",
                title  = st.session_state.get("jobTitle",""),
                company= st.session_state.get("companyName",""),
                city   = st.session_state.get("city","Germany"),
                descr  = st.session_state.get("roleDescription",""),
                tasks  = st.session_state.get("keyResponsibilities",""),
                must   = st.session_state.get("mustHaveSkills",""),
                nice   = st.session_state.get("niceToHaveSkills",""),
                salary = st.session_state.get("salaryRange",""),
                vacation = st.session_state.get("vacationDays",28),
                flexHours= st.session_state.get("flexibleHours","No"),
                remote = st.session_state.get("remoteWorkPolicy","On-site"),
                channels= st.session_state.get("desiredPublicationChannels","")
            )
        ad_text = chatgpt(ad_prompt, max_tokens=600)
        st.session_state["generatedJobAd"] = ad_text.strip()
        trace.log("job_ad_generated")

        # ── Email Template generation (EN) ──────────────────────────────
        if not st.session_state.get("generatedEmailTemplate"):
            email_prompt = (
                "Write a short English outreach email to a passive candidate for the role "
                "«{title}» at {company}. Include salary range {salary} {cur} and CTA to "
                "book a call."
            ).format(
                title=st.session_state.get("jobTitle",""),
                company=st.session_state.get("companyName",""),
                salary=st.session_state.get("salaryRange",""),
                cur   = st.session_state.get("currency","EUR")
            )
            email_text = chatgpt(email_prompt, max_tokens=300)
            st.session_state["generatedEmailTemplate"] = email_text.strip()
            trace.log("email_template_generated")

        # ── Dynamic Q: translation toggle ───────────────────────────────
        if (st.session_state["translationRequired"]
                and not st.session_state["languageOfAd"].startswith("Bilingual")):
            dq.enqueue(
                "language_of_ad",
                "Translation required but language set to one language only. "
                "Switch to bilingual?"
            )

        st.success("Final artefacts generated ✔ Scroll down for preview.")

    # ── 3 · Preview & export ────────────────────────────────────────────
    if st.session_state.get("generatedJobAd"):
        st.subheader("Job-Ad Preview")
        st.markdown(st.session_state["generatedJobAd"], unsafe_allow_html=False)

    if st.session_state.get("generatedEmailTemplate"):
        with st.expander("Candidate Email Template"):
            st.markdown(st.session_state["generatedEmailTemplate"])

    # ── 4 · Dynamic questions & trace viewer ────────────────────────────
    dq.render_pending_questions()
    with st.expander("Trace Log"):
        trace.render_ui()


# ────────────────────────────────────────────────────────────────────
#  MAIN SINGLE-PAGE WIZARD ROUTER
# ────────────────────────────────────────────────────────────────────
def _init_session():
    if "wizard_step" not in st.session_state:
        st.session_state["wizard_step"] = 1

def _next_step():
    st.session_state["wizard_step"] = min(st.session_state["wizard_step"] + 1, 8)

def _prev_step():
    st.session_state["wizard_step"] = max(st.session_state["wizard_step"] - 1, 1)

def main():
    st.set_page_config(page_title="Vacalyser Wizard", layout="wide")
    _init_session()

    step = st.session_state["wizard_step"]

    # ----------  router ----------
    if   step == 1: discovery_page()
    elif step == 2: job_company_page()
    elif step == 3: role_definition_page()
    elif step == 4: tasks_page()
    elif step == 5: skills_page()
    elif step == 6: compensation_page()
    elif step == 7: recruitment_page()
    elif step == 8: summary_page()

    # ----------  nav buttons ----------
    col_prev, col_next = st.columns([1, 1])
    with col_prev:
        if step > 1 and st.button("⬅️ Back"):
            _prev_step()
            st.experimental_rerun()
    with col_next:
        if step < 8 and st.button("Next ➡️"):
            _next_step()
            st.experimental_rerun()

if __name__ == "__main__":
    main()

