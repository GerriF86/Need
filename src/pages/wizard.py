# src/pages/wizard.py
from __future__ import annotations
import requests
from bs4 import BeautifulSoup
import streamlit as st
from src.config.keys import STEP_KEYS  # field definitions per step

# Utility: parse file content (PDF/DOCX/TXT) into text
def parse_file(file_bytes: bytes, file_name: str) -> str:
    import os
    ext = os.path.splitext(file_name)[1].lower()
    if ext == ".pdf":
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
    elif ext == ".docx":
        import docx
        doc = docx.Document(file_bytes)
        text = "\n".join(p.text for p in doc.paragraphs)
    elif ext == ".txt":
        text = file_bytes.decode("utf-8", errors="ignore")
    else:
        text = ""
    # Basic cleanup: collapse multiple spaces/newlines
    if text:
        text = " ".join(text.split())
    return text

# Utility: fetch text content from a URL (HTML or raw text)
def fetch_url_text(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        st.warning(f"Failed to fetch URL: {e}")
        return ""
    content_type = resp.headers.get("Content-Type", "")
    text = ""
    if "text/html" in content_type:
        soup = BeautifulSoup(resp.text, "html.parser")
        # Get visible text from HTML
        text = soup.get_text(separator=" ", strip=True)
    elif "pdf" in content_type or "application/pdf" in content_type:
        text = parse_file(resp.content, "file.pdf")
    elif "msword" in content_type or "officedocument" in content_type:
        text = parse_file(resp.content, "file.docx")
    else:
        # Fallback for plain text or other types
        text = resp.text
    return text

# Utility: extract known fields from raw text into session_state
def match_and_store_keys(raw_text: str) -> None:
    if not raw_text:
        return
    # Define mapping of session keys to identifiable labels in text
    label_map = {
        "job_title": "Job Title:",
        "company_name": "Company Name:",
        "brand_name": "Brand Name:",
        "headquarters_location": "HQ Location:",
        "company_website": "Company Website:",
        "date_of_employment_start": "Date of Employment Start:",
        "job_type": "Job Type:",
        "contract_type": "Contract Type:",
        "job_level": "Job Level:",
        "city": "City (Job Location):",
        "team_structure": "Team Structure:",
        "role_description": "Role Description:",
        "reports_to": "Reports To:",
        "supervises": "Supervises:",
        "role_type": "Role Type:",
        "role_priority_projects": "Role Priority Projects:",
        "travel_requirements": "Travel Requirements:",
        "work_schedule": "Work Schedule:",
        "role_keywords": "Role Keywords:",
        "decision_making_authority": "Decision Making Authority:",
        "role_performance_metrics": "Role Performance Metrics:",
        "task_list": "Task List:",
        "key_responsibilities": "Key Responsibilities:",
        "technical_tasks": "Technical Tasks:",
        "managerial_tasks": "Managerial Tasks:",
        "administrative_tasks": "Administrative Tasks:",
        "customer_facing_tasks": "Customer-Facing Tasks:",
        "internal_reporting_tasks": "Internal Reporting Tasks:",
        "performance_tasks": "Performance Tasks:",
        "innovation_tasks": "Innovation Tasks:",
        "task_prioritization": "Task Prioritization:",
        "hard_skills": "Hard Skills:",
        "soft_skills": "Soft Skills:",
        "must_have_skills": "Must-Have Skills:",
        "nice_to_have_skills": "Nice-to-Have Skills:",
        "certifications_required": "Certifications Required:",
        "language_requirements": "Language Requirements:",
        "tool_proficiency": "Tool Proficiency:",
        "domain_expertise": "Domain Expertise:",
        "leadership_competencies": "Leadership Competencies:",
        "technical_stack": "Technical Stack:",
        "industry_experience": "Industry Experience:",
        "analytical_skills": "Analytical Skills:",
        "communication_skills": "Communication Skills:",
        "project_management_skills": "Project Management Skills:",
        "soft_requirement_details": "Additional Soft Requirements:",
        "visa_sponsorship": "Visa Sponsorship:",
        "salary_range": "Salary Range:",
        "currency": "Currency:",
        "pay_frequency": "Pay Frequency:",
        "commission_structure": "Commission Structure:",
        "bonus_scheme": "Bonus Scheme:",
        "vacation_days": "Vacation Days:",
        "flexible_hours": "Flexible Hours:",
        "remote_work_policy": "Remote Work Policy:",
        "relocation_assistance": "Relocation Assistance:",
        "childcare_support": "Childcare Support:",
        "recruitment_steps": "Recruitment Steps:",
        "recruitment_timeline": "Recruitment Timeline:",
        "number_of_interviews": "Number of Interviews:",
        "interview_format": "Interview Format:",
        "assessment_tests": "Assessment Tests:",
        "onboarding_process_overview": "Onboarding Process Overview:",
        "recruitment_contact_email": "Recruitment Contact Email:",
        "recruitment_contact_phone": "Recruitment Contact Phone:",
        "application_instructions": "Application Instructions:",
        "language_of_ad": "Language of Ad:",
        "translation_required": "Translation Required:",
        "employer_branding_elements": "Employer Branding Elements:",
        "desired_publication_channels": "Desired Publication Channels:",
        "internal_job_id": "Internal Job ID:",
        "ad_seniority_tone": "Ad Seniority Tone:",
        "ad_length_preference": "Ad Length Preference:",
        "deadline_urgency": "Deadline Urgency:",
        "company_awards": "Company Awards:",
        "diversity_inclusion_statement": "Diversity & Inclusion Statement:",
        "legal_disclaimers": "Legal Disclaimers:",
        "social_media_links": "Social Media Links:",
        "video_introduction_option": "Video Introduction Option:",
        "comments_internal": "Comments (Internal):",
    }
    # Loop through each known label and extract the corresponding value
    text = raw_text
    for key, label in label_map.items():
        if label in text:
            start = text.find(label) + len(label)
            end_line = text.find("\n", start)
            if end_line == -1:
                end_line = len(text)
            value = text[start:end_line].strip()
            # Remove any trailing punctuation or colon
            value = value.lstrip(": ").rstrip()
            if value:
                st.session_state[key] = value

# Step 1: Start Discovery (Input source analysis)
def start_discovery_page():
    import streamlit as st
    from your_parsers_module import parse_file, fetch_url_text, match_and_store_keys  # Update to your actual module

    # Language toggle (session-level)
    lang = st.radio("🌐 Sprache / Language", ("Deutsch", "English"), horizontal=True)

    # RoleCraft Main Titles
    if lang == "Deutsch":
        st.title("🚀 Erstelle die perfekte Stellenbeschreibung")
        st.subheader("Von der ersten Idee bis zur fertigen Ausschreibung.")
        intro_text = (
            "Willkommen bei **RoleCraft**.\n\n"
            "Starte mit einem Jobtitel oder lade eine Anzeige hoch.\n"
            "Unser KI-gestützter Wizard analysiert, ergänzt fehlende Infos und begleitet dich sicher zum perfekten Profil."
        )
        button_job = "➕ Jobtitel eingeben"
        button_upload = "📂 PDF / DOCX hochladen"
    else:
        st.title("🚀 Create the Perfect Job Description")
        st.subheader("From the first idea to a fully crafted profile.")
        intro_text = (
            "Welcome to **RoleCraft**.\n\n"
            "Start with a job title or upload an ad.\n"
            "Our AI-powered wizard analyzes, fills gaps, and guides you seamlessly to a perfect profile."
        )
        button_job = "➕ Enter Job Title"
        button_upload = "📂 Upload PDF / DOCX"

    # Main Intro Text
    st.markdown(intro_text)

    # Vacalyser Upload Section
    st.header("Vacalyser – Start Discovery")
    st.write("Enter a job title and either a link to an existing job ad or upload a job description file. "
             "The wizard will analyze the content and auto-fill relevant fields where possible.")

    col1, col2 = st.columns([1, 1])
    with col1:
        job_title = st.text_input(button_job, value=st.session_state.get("job_title", ""), placeholder="e.g. Senior Data Scientist")
        if job_title:
            st.session_state["job_title"] = job_title

        input_url = st.text_input("🔗 Job Ad URL (optional)", value=st.session_state.get("input_url", ""))
        if input_url:
            st.session_state["input_url"] = input_url

    with col2:
        uploaded_file = st.file_uploader(button_upload, type=["pdf", "docx", "txt"])
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            raw_text = parse_file(file_bytes, uploaded_file.name)
            if raw_text:
                st.session_state["uploaded_file"] = raw_text
                st.success("✅ File uploaded and text extracted.")
            else:
                st.error("❌ Failed to extract text from the uploaded file.")

    analyze_clicked = st.button("🔎 Analyze Sources")
    if analyze_clicked:
        raw_text = ""
        if st.session_state.get("uploaded_file"):
            raw_text = st.session_state["uploaded_file"]
        elif st.session_state.get("input_url"):
            raw_text = fetch_url_text(st.session_state["input_url"])

        if not raw_text:
            st.warning("⚠️ Please provide a valid URL or upload a file before analysis.")
        else:
            st.session_state["parsed_data_raw"] = raw_text
            try:
                match_and_store_keys(raw_text)
                st.success("🎯 Analysis complete! Key details auto-filled.")
                if "trace_events" not in st.session_state:
                    st.session_state["trace_events"] = []
                st.session_state.trace_events.append("Auto-extracted fields from provided job description.")
            except Exception as e:
                st.error(f"❌ Analysis failed: {e}")
# Helper functions to render static forms for steps 2-7
def render_step2_static():
    st.title("Step 2: Basic Job & Company Info")
    company_name = st.text_input("Company Name", value=st.session_state.get("company_name", ""), placeholder="e.g. Tech Corp Ltd.")
    brand_name = st.text_input("Brand Name (if different)", value=st.session_state.get("brand_name", ""), placeholder="e.g. Parent Company Inc.")
    headquarters_location = st.text_input("Headquarters Location", value=st.session_state.get("headquarters_location", ""), placeholder="e.g. Berlin, Germany")
    company_website = st.text_input("Company Website", value=st.session_state.get("company_website", ""), placeholder="e.g. https://company.com")
    date_of_start = st.text_input("Preferred Start Date", value=st.session_state.get("date_of_employment_start", ""), placeholder="e.g. ASAP or 2025-01-15")
    job_type = st.selectbox("Job Type", ["Full-Time", "Part-Time", "Internship", "Freelance", "Volunteer", "Other"], 
                             index=0 if not st.session_state.get("job_type") else 0)  # default to first; state will update on submit
    contract_type = st.selectbox("Contract Type", ["Permanent", "Fixed-Term", "Contract", "Other"], index=0 if not st.session_state.get("contract_type") else 0)
    job_level = st.selectbox("Job Level", ["Entry-level", "Mid-level", "Senior", "Director", "C-level", "Other"], index=0 if not st.session_state.get("job_level") else 0)
    city = st.text_input("City (Job Location)", value=st.session_state.get("city", ""), placeholder="e.g. London")
    team_structure = st.text_area("Team Structure", value=st.session_state.get("team_structure", ""), placeholder="Describe the team setup, reporting hierarchy, etc.")
    return {
        "company_name": company_name,
        "brand_name": brand_name,
        "headquarters_location": headquarters_location,
        "company_website": company_website,
        "date_of_employment_start": date_of_start,
        "job_type": job_type,
        "contract_type": contract_type,
        "job_level": job_level,
        "city": city,
        "team_structure": team_structure
    }

def render_step3_static():
    st.title("Step 3: Role Definition")
    role_description = st.text_area("Role Description", value=st.session_state.get("role_description", ""), placeholder="High-level summary of the role...")
    reports_to = st.text_input("Reports To", value=st.session_state.get("reports_to", ""), placeholder="Position this role reports to")
    supervises = st.text_area("Supervises", value=st.session_state.get("supervises", ""), placeholder="List positions or teams this role supervises")
    role_type = st.selectbox("Role Type", ["Individual Contributor", "Team Lead", "Manager", "Director", "Executive", "Other"], index=0 if not st.session_state.get("role_type") else 0)
    role_priority_projects = st.text_area("Priority Projects", value=st.session_state.get("role_priority_projects", ""), placeholder="Key projects or initiatives for this role")
    travel_requirements = st.text_input("Travel Requirements", value=st.session_state.get("travel_requirements", ""), placeholder="e.g. Up to 20% travel required")
    work_schedule = st.text_input("Work Schedule", value=st.session_state.get("work_schedule", ""), placeholder="e.g. Mon-Fri 9-5, rotating shifts")
    role_keywords = st.text_area("Role Keywords", value=st.session_state.get("role_keywords", ""), placeholder="Keywords for this role (for SEO or analytics)")
    decision_authority = st.text_input("Decision Making Authority", value=st.session_state.get("decision_making_authority", ""), placeholder="Scope of decisions (e.g. budget up to $10k)")
    performance_metrics = st.text_area("Role Performance Metrics", value=st.session_state.get("role_performance_metrics", ""), placeholder="KPIs or success metrics for this role")
    return {
        "role_description": role_description,
        "reports_to": reports_to,
        "supervises": supervises,
        "role_type": role_type,
        "role_priority_projects": role_priority_projects,
        "travel_requirements": travel_requirements,
        "work_schedule": work_schedule,
        "role_keywords": role_keywords,
        "decision_making_authority": decision_authority,
        "role_performance_metrics": performance_metrics
    }

def render_step4_static():
    st.title("Step 4: Tasks & Responsibilities")
    task_list = st.text_area("General Task List", value=st.session_state.get("task_list", ""), placeholder="Bullet points of day-to-day tasks")
    key_responsibilities = st.text_area("Key Responsibilities", value=st.session_state.get("key_responsibilities", ""), placeholder="Major areas of responsibility")
    technical_tasks = st.text_area("Technical Tasks", value=st.session_state.get("technical_tasks", ""), placeholder="Specialized/technical duties")
    managerial_tasks = st.text_area("Managerial Tasks", value=st.session_state.get("managerial_tasks", ""), placeholder="Managerial or leadership duties")
    administrative_tasks = st.text_area("Administrative Tasks", value=st.session_state.get("administrative_tasks", ""), placeholder="Administrative or support tasks")
    customer_facing_tasks = st.text_area("Customer-Facing Tasks", value=st.session_state.get("customer_facing_tasks", ""), placeholder="Client-facing duties")
    internal_reporting_tasks = st.text_area("Internal Reporting Tasks", value=st.session_state.get("internal_reporting_tasks", ""), placeholder="Reporting and documentation tasks")
    performance_tasks = st.text_area("Performance-Related Tasks", value=st.session_state.get("performance_tasks", ""), placeholder="Tasks tied to performance metrics")
    innovation_tasks = st.text_area("Innovation Tasks", value=st.session_state.get("innovation_tasks", ""), placeholder="R&D or innovation-related tasks")
    task_prioritization = st.text_area("Task Prioritization", value=st.session_state.get("task_prioritization", ""), placeholder="How tasks are prioritized")
    return {
        "task_list": task_list,
        "key_responsibilities": key_responsibilities,
        "technical_tasks": technical_tasks,
        "managerial_tasks": managerial_tasks,
        "administrative_tasks": administrative_tasks,
        "customer_facing_tasks": customer_facing_tasks,
        "internal_reporting_tasks": internal_reporting_tasks,
        "performance_tasks": performance_tasks,
        "innovation_tasks": innovation_tasks,
        "task_prioritization": task_prioritization
    }

def render_step5_static():
    st.title("Step 5: Skills & Competencies")
    hard_skills = st.text_area("Hard Skills", value=st.session_state.get("hard_skills", ""), placeholder="Technical or job-specific skills")
    soft_skills = st.text_area("Soft Skills", value=st.session_state.get("soft_skills", ""), placeholder="Communication, teamwork, leadership, etc.")
    must_have_skills = st.text_area("Must-Have Skills", value=st.session_state.get("must_have_skills", ""), placeholder="Non-negotiable requirements")
    nice_to_have_skills = st.text_area("Nice-to-Have Skills", value=st.session_state.get("nice_to_have_skills", ""), placeholder="Preferred additional skills")
    certifications_required = st.text_area("Certifications Required", value=st.session_state.get("certifications_required", ""), placeholder="Degrees or certifications (if any)")
    language_requirements = st.text_area("Language Requirements", value=st.session_state.get("language_requirements", ""), placeholder="e.g. English C1, French B2")
    tool_proficiency = st.text_area("Tool Proficiency", value=st.session_state.get("tool_proficiency", ""), placeholder="Software or tools expertise (e.g. Excel, AWS)")
    domain_expertise = st.text_area("Domain Expertise", value=st.session_state.get("domain_expertise", ""), placeholder="Industry/field expertise (e.g. finance, AI)")
    leadership_competencies = st.text_area("Leadership Competencies", value=st.session_state.get("leadership_competencies", ""), placeholder="For managerial roles: mentoring, strategic thinking, etc.")
    technical_stack = st.text_area("Technical Stack", value=st.session_state.get("technical_stack", ""), placeholder="Technologies used (for technical roles)")
    industry_experience = st.text_input("Industry Experience", value=st.session_state.get("industry_experience", ""), placeholder="Years of experience in relevant industry")
    analytical_skills = st.text_input("Analytical Skills", value=st.session_state.get("analytical_skills", ""), placeholder="Analytical or critical-thinking skills")
    communication_skills = st.text_input("Communication Skills", value=st.session_state.get("communication_skills", ""), placeholder="Written and verbal communication skills")
    project_management_skills = st.text_input("Project Management Skills", value=st.session_state.get("project_management_skills", ""), placeholder="Ability to plan, execute, and manage projects")
    soft_requirement_details = st.text_area("Additional Soft Requirements", value=st.session_state.get("soft_requirement_details", ""), placeholder="Other personality or work style requirements")
    visa_sponsorship = st.selectbox("Visa Sponsorship", ["No", "Yes", "Case-by-Case"], index=0 if not st.session_state.get("visa_sponsorship") else 0)
    return {
        "hard_skills": hard_skills,
        "soft_skills": soft_skills,
        "must_have_skills": must_have_skills,
        "nice_to_have_skills": nice_to_have_skills,
        "certifications_required": certifications_required,
        "language_requirements": language_requirements,
        "tool_proficiency": tool_proficiency,
        "domain_expertise": domain_expertise,
        "leadership_competencies": leadership_competencies,
        "technical_stack": technical_stack,
        "industry_experience": industry_experience,
        "analytical_skills": analytical_skills,
        "communication_skills": communication_skills,
        "project_management_skills": project_management_skills,
        "soft_requirement_details": soft_requirement_details,
        "visa_sponsorship": visa_sponsorship
    }

def render_step6_static():
    st.title("Step 6: Compensation & Benefits")
    salary_range = st.text_input("Salary Range", value=st.session_state.get("salary_range", ""), placeholder="e.g. 50,000 - 60,000 EUR")
    currency = st.selectbox("Currency", ["EUR", "USD", "GBP", "Other"], index=0 if not st.session_state.get("currency") else 0)
    pay_frequency = st.selectbox("Pay Frequency", ["Annual", "Monthly", "Bi-weekly", "Weekly", "Other"], index=0 if not st.session_state.get("pay_frequency") else 0)
    commission_structure = st.text_input("Commission Structure", value=st.session_state.get("commission_structure", ""), placeholder="Details of any commission")
    bonus_scheme = st.text_input("Bonus Scheme", value=st.session_state.get("bonus_scheme", ""), placeholder="Details of bonus or incentive scheme")
    vacation_days = st.text_input("Vacation Days", value=st.session_state.get("vacation_days", ""), placeholder="e.g. 25 days")
    flexible_hours = st.selectbox("Flexible Hours", ["No", "Yes", "Partial/Flex"], index=0 if not st.session_state.get("flexible_hours") else 0)
    remote_policy = st.selectbox("Remote Work Policy", ["On-site", "Hybrid", "Full Remote", "Other"], index=0 if not st.session_state.get("remote_work_policy") else 0)
    relocation_assistance = st.selectbox("Relocation Assistance", ["No", "Yes", "Case-by-Case"], index=0 if not st.session_state.get("relocation_assistance") else 0)
    childcare_support = st.selectbox("Childcare Support", ["No", "Yes", "Case-by-Case"], index=0 if not st.session_state.get("childcare_support") else 0)
    return {
        "salary_range": salary_range,
        "currency": currency,
        "pay_frequency": pay_frequency,
        "commission_structure": commission_structure,
        "bonus_scheme": bonus_scheme,
        "vacation_days": vacation_days,
        "flexible_hours": flexible_hours,
        "remote_work_policy": remote_policy,
        "relocation_assistance": relocation_assistance,
        "childcare_support": childcare_support
    }

def render_step7_static():
    st.title("Step 7: Recruitment Process")
    recruitment_steps = st.text_area("Recruitment Steps", value=st.session_state.get("recruitment_steps", ""), placeholder="Outline the hiring process steps (e.g. screening, 2 interviews, etc.)")
    recruitment_timeline = st.text_input("Recruitment Timeline", value=st.session_state.get("recruitment_timeline", ""), placeholder="Estimated time from application to offer")
    number_of_interviews = st.text_input("Number of Interviews", value=st.session_state.get("number_of_interviews", ""), placeholder="e.g. 3")
    interview_format = st.text_input("Interview Format", value=st.session_state.get("interview_format", ""), placeholder="e.g. Phone, On-site, Video")
    assessment_tests = st.text_area("Assessment Tests", value=st.session_state.get("assessment_tests", ""), placeholder="Any tests or assignments for candidates?")
    onboarding_process = st.text_area("Onboarding Process Overview", value=st.session_state.get("onboarding_process_overview", ""), placeholder="Brief overview of post-hire onboarding")
    contact_email = st.text_input("Recruitment Contact Email", value=st.session_state.get("recruitment_contact_email", ""), placeholder="Email for applications or inquiries")
    contact_phone = st.text_input("Recruitment Contact Phone", value=st.session_state.get("recruitment_contact_phone", ""), placeholder="Contact phone number (if applicable)")
    application_instructions = st.text_area("Application Instructions", value=st.session_state.get("application_instructions", ""), placeholder="How to apply (e.g. via portal or email)")
    return {
        "recruitment_steps": recruitment_steps,
        "recruitment_timeline": recruitment_timeline,
        "number_of_interviews": number_of_interviews,
        "interview_format": interview_format,
        "assessment_tests": assessment_tests,
        "onboarding_process_overview": onboarding_process,
        "recruitment_contact_email": contact_email,
        "recruitment_contact_phone": contact_phone,
        "application_instructions": application_instructions
    }

# Step 8: Additional Info & Final Summary (no dynamic questions, just summary)
def render_step8():
    st.title("Step 8: Additional Information & Final Review")
    st.subheader("Additional Metadata")
    parsed_data = st.text_area("Parsed Data (Raw)", value=st.session_state.get("parsed_data_raw", ""), placeholder="(Auto-generated raw text from analysis)", help="This is the raw text extracted from the provided source, if any.")
    language_of_ad = st.text_input("Language of Ad", value=st.session_state.get("language_of_ad", ""), placeholder="e.g. English, German")
    translation_required = st.selectbox("Translation Required?", ["No", "Yes"], index=0 if not st.session_state.get("translation_required") else 0)
    branding_elements = st.text_area("Employer Branding Elements", value=st.session_state.get("employer_branding_elements", ""), placeholder="Company culture or branding highlights to include")
    publication_channels = st.text_area("Desired Publication Channels", value=st.session_state.get("desired_publication_channels", ""), placeholder="Where this ad will be posted (if specific)")
    internal_job_id = st.text_input("Internal Job ID", value=st.session_state.get("internal_job_id", ""), placeholder="Internal reference ID for this position")
    ad_seniority_tone = st.selectbox("Ad Seniority Tone", ["Casual", "Formal", "Neutral", "Enthusiastic"], index=0 if not st.session_state.get("ad_seniority_tone") else 0)
    ad_length_pref = st.selectbox("Ad Length Preference", ["Short & Concise", "Detailed", "Flexible"], index=0 if not st.session_state.get("ad_length_preference") else 0)
    deadline_urgency = st.text_input("Application Deadline/Urgency", value=st.session_state.get("deadline_urgency", ""), placeholder="e.g. Apply by 30 June; Urgent fill")
    company_awards = st.text_area("Company Awards", value=st.session_state.get("company_awards", ""), placeholder="Notable awards or recognitions of the company")
    diversity_statement = st.text_area("Diversity & Inclusion Statement", value=st.session_state.get("diversity_inclusion_statement", ""), placeholder="Company's D&I commitment statement")
    legal_disclaimers = st.text_area("Legal Disclaimers", value=st.session_state.get("legal_disclaimers", ""), placeholder="Any legal or compliance text for the ad")
    social_links = st.text_area("Social Media Links", value=st.session_state.get("social_media_links", ""), placeholder="Links to company social media profiles (if included in ad)")
    video_option = st.selectbox("Video Introduction Option", ["No", "Yes"], index=0 if not st.session_state.get("video_introduction_option") else 0)
    comments_internal = st.text_area("Comments (Internal)", value=st.session_state.get("comments_internal", ""), placeholder="Any internal comments or notes")
    # Save all step8 fields into session_state
    st.session_state["parsed_data_raw"] = parsed_data
    st.session_state["language_of_ad"] = language_of_ad
    st.session_state["translation_required"] = translation_required
    st.session_state["employer_branding_elements"] = branding_elements
    st.session_state["desired_publication_channels"] = publication_channels
    st.session_state["internal_job_id"] = internal_job_id
    st.session_state["ad_seniority_tone"] = ad_seniority_tone
    st.session_state["ad_length_preference"] = ad_length_pref
    st.session_state["deadline_urgency"] = deadline_urgency
    st.session_state["company_awards"] = company_awards
    st.session_state["diversity_inclusion_statement"] = diversity_statement
    st.session_state["legal_disclaimers"] = legal_disclaimers
    st.session_state["social_media_links"] = social_links
    st.session_state["video_introduction_option"] = video_option
    st.session_state["comments_internal"] = comments_internal

    # Display Final Summary of all fields
    st.subheader("Final Summary")
    # We iterate through all steps and show each field and its value
    for step, keys in STEP_KEYS.items():
        for key in keys:
            label = key.replace("_", " ").title()
            value = st.session_state.get(key, "")
            st.markdown(f"**{label}:** {value}")
        if step == 2 or step == 3 or step == 4 or step == 5 or step == 6 or step == 7:
            st.markdown("---")
    st.info("Review the above summary. You can go back to edit any step, or proceed to finalize the job ad.")

# Main function to orchestrate the wizard steps
def run_wizard():
    step = st.session_state.get("wizard_step", 1)
    if step == 1:
        start_discovery_page()
    elif step == 2:
        # Step 2: static form + dynamic questions
        with st.form("step2_form"):
            values = render_step2_static()
            submitted = st.form_submit_button("Next")
        if submitted:
            # Update session_state with form inputs
            for k, v in values.items():
                st.session_state[k] = v
            # Notify trigger engine for each updated key
            for k in STEP_KEYS[2]:
                st.session_state.trigger_engine.notify_change(k, st.session_state)
            # Determine missing fields for dynamic Q
            missing = [k for k in STEP_KEYS[2] if not st.session_state[k]]
            if missing:
                st.session_state["step2_static_submitted"] = True
                st.session_state.trace_events.append(f"Step 2 submitted. Missing: {missing}")
                st.rerun()
            else:
                st.session_state["step2_static_submitted"] = False
                st.session_state["wizard_step"] = 3
                st.session_state.trace_events.append("Step 2 submitted. All fields provided.")
                st.rerun()
        # Dynamic question phase for step 2
        if st.session_state.get("step2_static_submitted"):
            # Identify up to 5 missing keys (already computed above if we are here)
            missing_keys = [k for k in STEP_KEYS[2] if not st.session_state[k]]
            st.info("Please provide additional details for the following fields:")
            for key in missing_keys[:5]:
                # Friendly label for the field
                label = key.replace("_", " ").title()
                # Use text_area for longer inputs and text_input for short ones
                if "description" in key or "tasks" in key or "details" in key or "comments" in key:
                    st.text_area(label, key=key)
                else:
                    st.text_input(label, key=key)
            if st.button("Continue", key="continue_step2"):
                # Notify trigger engine for any newly filled fields
                for k in STEP_KEYS[2]:
                    st.session_state.trigger_engine.notify_change(k, st.session_state)
                st.session_state["step2_static_submitted"] = False
                st.session_state["wizard_step"] = 3
                st.session_state.trace_events.append("Step 2 dynamic questions answered, continuing to step 3.")
                st.rerun()
    elif step == 3:
        with st.form("step3_form"):
            values = render_step3_static()
            submitted = st.form_submit_button("Next")
        if submitted:
            for k, v in values.items():
                st.session_state[k] = v
            for k in STEP_KEYS[3]:
                st.session_state.trigger_engine.notify_change(k, st.session_state)
            missing = [k for k in STEP_KEYS[3] if not st.session_state[k]]
            if missing:
                st.session_state["step3_static_submitted"] = True
                st.session_state.trace_events.append(f"Step 3 submitted. Missing: {missing}")
                st.experimental_rerun()
            else:
                st.session_state["step3_static_submitted"] = False
                st.session_state["wizard_step"] = 4
                st.session_state.trace_events.append("Step 3 submitted. All fields provided.")
                st.rerun()
        if st.session_state.get("step3_static_submitted"):
            missing_keys = [k for k in STEP_KEYS[3] if not st.session_state[k]]
            st.info("Please provide additional details for the following fields:")
            for key in missing_keys[:5]:
                label = key.replace("_", " ").title()
                if "role_description" in key or "supervises" in key or "priority_projects" in key or "keywords" in key or "metrics" in key:
                    st.text_area(label, key=key)
                else:
                    st.text_input(label, key=key)
            if st.button("Continue", key="continue_step3"):
                for k in STEP_KEYS[3]:
                    st.session_state.trigger_engine.notify_change(k, st.session_state)
                st.session_state["step3_static_submitted"] = False
                st.session_state["wizard_step"] = 4
                st.session_state.trace_events.append("Step 3 dynamic questions answered, continuing to step 4.")
                st.rerun()
    elif step == 4:
        with st.form("step4_form"):
            values = render_step4_static()
            submitted = st.form_submit_button("Next")
        if submitted:
            for k, v in values.items():
                st.session_state[k] = v
            for k in STEP_KEYS[4]:
                st.session_state.trigger_engine.notify_change(k, st.session_state)
            missing = [k for k in STEP_KEYS[4] if not st.session_state[k]]
            if missing:
                st.session_state["step4_static_submitted"] = True
                st.session_state.trace_events.append(f"Step 4 submitted. Missing: {missing}")
                st.rerun()
            else:
                st.session_state["step4_static_submitted"] = False
                st.session_state["wizard_step"] = 5
                st.session_state.trace_events.append("Step 4 submitted. All fields provided.")
                st.rerun()
        if st.session_state.get("step4_static_submitted"):
            missing_keys = [k for k in STEP_KEYS[4] if not st.session_state[k]]
            st.info("Please provide additional details for the following fields:")
            for key in missing_keys[:5]:
                label = key.replace("_", " ").title()
                st.text_area(label, key=key)  # most in step 4 are multi-line
            if st.button("Continue", key="continue_step4"):
                for k in STEP_KEYS[4]:
                    st.session_state.trigger_engine.notify_change(k, st.session_state)
                st.session_state["step4_static_submitted"] = False
                st.session_state["wizard_step"] = 5
                st.session_state.trace_events.append("Step 4 dynamic questions answered, continuing to step 5.")
                st.rerun()
    elif step == 5:
        with st.form("step5_form"):
            values = render_step5_static()
            submitted = st.form_submit_button("Next")
        if submitted:
            for k, v in values.items():
                st.session_state[k] = v
            for k in STEP_KEYS[5]:
                st.session_state.trigger_engine.notify_change(k, st.session_state)
            missing = [k for k in STEP_KEYS[5] if not st.session_state[k]]
            if missing:
                st.session_state["step5_static_submitted"] = True
                st.session_state.trace_events.append(f"Step 5 submitted. Missing: {missing}")
                st.rerun()
            else:
                st.session_state["step5_static_submitted"] = False
                st.session_state["wizard_step"] = 6
                st.session_state.trace_events.append("Step 5 submitted. All fields provided.")
                st.rerun()
        if st.session_state.get("step5_static_submitted"):
            missing_keys = [k for k in STEP_KEYS[5] if not st.session_state[k]]
            st.info("Please provide additional details for the following fields:")
            for key in missing_keys[:5]:
                label = key.replace("_", " ").title()
                if key in ("hard_skills", "soft_skills", "must_have_skills", "nice_to_have_skills",
                           "certifications_required", "language_requirements", "tool_proficiency",
                           "domain_expertise", "leadership_competencies", "technical_stack", "soft_requirement_details"):
                    st.text_area(label, key=key)
                else:
                    st.text_input(label, key=key)
            if st.button("Continue", key="continue_step5"):
                for k in STEP_KEYS[5]:
                    st.session_state.trigger_engine.notify_change(k, st.session_state)
                st.session_state["step5_static_submitted"] = False
                st.session_state["wizard_step"] = 6
                st.session_state.trace_events.append("Step 5 dynamic questions answered, continuing to step 6.")
                st.rerun()
    elif step == 6:
        with st.form("step6_form"):
            values = render_step6_static()
            submitted = st.form_submit_button("Next")
        if submitted:
            for k, v in values.items():
                st.session_state[k] = v
            for k in STEP_KEYS[6]:
                st.session_state.trigger_engine.notify_change(k, st.session_state)
            missing = [k for k in STEP_KEYS[6] if not st.session_state[k]]
            if missing:
                st.session_state["step6_static_submitted"] = True
                st.session_state.trace_events.append(f"Step 6 submitted. Missing: {missing}")
                st.rerun()
            else:
                st.session_state["step6_static_submitted"] = False
                st.session_state["wizard_step"] = 7
                st.session_state.trace_events.append("Step 6 submitted. All fields provided.")
                st.rerun()
        if st.session_state.get("step6_static_submitted"):
            missing_keys = [k for k in STEP_KEYS[6] if not st.session_state[k]]
            st.info("Please provide additional details for the following fields:")
            for key in missing_keys[:5]:
                label = key.replace("_", " ").title()
                # Most comp & benefits fields are short text or select; use text_input for any missing
                st.text_input(label, key=key)
            if st.button("Continue", key="continue_step6"):
                for k in STEP_KEYS[6]:
                    st.session_state.trigger_engine.notify_change(k, st.session_state)
                st.session_state["step6_static_submitted"] = False
                st.session_state["wizard_step"] = 7
                st.session_state.trace_events.append("Step 6 dynamic questions answered, continuing to step 7.")
                st.rerun()
    elif step == 7:
        with st.form("step7_form"):
            values = render_step7_static()
            submitted = st.form_submit_button("Next")
        if submitted:
            for k, v in values.items():
                st.session_state[k] = v
            for k in STEP_KEYS[7]:
                st.session_state.trigger_engine.notify_change(k, st.session_state)
            missing = [k for k in STEP_KEYS[7] if not st.session_state[k]]
            if missing:
                st.session_state["step7_static_submitted"] = True
                st.session_state.trace_events.append(f"Step 7 submitted. Missing: {missing}")
                st.rerun()
            else:
                st.session_state["step7_static_submitted"] = False
                st.session_state["wizard_step"] = 8
                st.session_state.trace_events.append("Step 7 submitted. All fields provided.")
                st.rerun()
        if st.session_state.get("step7_static_submitted"):
            missing_keys = [k for k in STEP_KEYS[7] if not st.session_state[k]]
            st.info("Please provide additional details for the following fields:")
            for key in missing_keys[:5]:
                label = key.replace("_", " ").title()
                if "steps" in key or "tests" in key or "overview" in key or "instructions" in key:
                    st.text_area(label, key=key)
                else:
                    st.text_input(label, key=key)
            if st.button("Continue", key="continue_step7"):
                for k in STEP_KEYS[7]:
                    st.session_state.trigger_engine.notify_change(k, st.session_state)
                st.session_state["step7_static_submitted"] = False
                st.session_state["wizard_step"] = 8
                st.session_state.trace_events.append("Step 7 dynamic questions answered, continuing to step 8.")
                st.rerun()
    elif step == 8:
        render_step8()
    else:
        # Edge case: reset if out-of-bounds
        st.session_state["wizard_step"] = 1
        st.rerun()

    # Navigation controls (Back/Next) at bottom, controlling step transitions
    if step > 1:
        if st.button("⬅️ Back"):
            # If going back from a step where dynamic Q was open, reset its flag
            if st.session_state.get(f"step{step}_static_submitted"):
                st.session_state[f"step{step}_static_submitted"] = False
            st.session_state["wizard_step"] -= 1
            st.rerun()
    if step < 8 and not st.session_state.get(f"step{step}_static_submitted", False):
        if st.button("Next ➡"):
            # Increment step if no dynamic questions are pending
            st.session_state["wizard_step"] += 1
            st.rerun()
