import streamlit as st
from src.models.job_models import JobSpec
from src.agents.vacancy_agent import auto_fill_job_spec

# Initialize or retrieve the JobSpec object in session_state
if "job_spec" not in st.session_state:
    st.session_state["job_spec"] = JobSpec()  # start with empty/default values
job_spec: JobSpec = st.session_state["job_spec"]

st.title("🚀 Vacalyser – Vacancy Creation Wizard")
st.markdown("Fill out the sections below to create a comprehensive job vacancy posting. "
            "Sections will unlock as you complete the previous ones.")

# Section 1: Basic Job & Company Info
with st.expander("1️⃣ Basic Job & Company Info", expanded=True):
    job_spec.job_title = st.text_input("Job Title *", value=job_spec.job_title or "")
    job_spec.company_name = st.text_input("Company Name *", value=job_spec.company_name or "")
    job_spec.brand_name = st.text_input("Brand Name (if different)", value=job_spec.brand_name or "")
    job_spec.headquarters_location = st.text_input("Headquarters Location", value=job_spec.headquarters_location or "")
    job_spec.company_website = st.text_input("Company Website", value=job_spec.company_website or "")
    job_spec.date_of_employment_start = st.text_input("Preferred Start Date", value=job_spec.date_of_employment_start or "")
    # ... (more inputs for job_type, contract_type, etc., possibly using selectbox for constrained choices)
    
    # Option to auto-fill via AI (Analyze Sources)
    st.markdown("**Optional:** Provide a job ad URL or upload a job description file to auto-fill fields:")
    col1, col2 = st.columns([1, 1])
    with col1:
        input_url = st.text_input("Job Ad/Company URL", "")
    with col2:
        uploaded_file = st.file_uploader("Upload Job Ad (PDF, DOCX, TXT)")
    if st.button("🔍 Analyze Sources with AI"):
        if not input_url and not uploaded_file:
            st.warning("Please provide a URL or upload a file for analysis.")
        else:
            file_bytes = uploaded_file.read() if uploaded_file else None
            file_name = uploaded_file.name if uploaded_file else ""
            with st.spinner("Analyzing..."):
                data = auto_fill_job_spec(input_url, file_bytes, file_name)
            if data:
                # Update the job_spec model with extracted data
                try:
                    st.session_state["job_spec"] = JobSpec(**data)  # validate and assign
                    job_spec = st.session_state["job_spec"]
                    st.success("Fields auto-filled from the provided source!")
                except Exception as e:
                    st.error(f"Auto-fill returned invalid data: {e}")
            else:
                st.info("No data extracted. Please fill in the details manually.")
    # Next Section trigger:
    if st.button("Next ➡️"):
        # Basic validation: require job_title and company_name at least
        if not job_spec.job_title or not job_spec.company_name:
            st.error("Please fill required fields (Job Title and Company Name) before proceeding.")
        else:
            st.session_state["current_step"] = 2

# Section 2: Role Definition (visible after Section 1 is completed)
if st.session_state.get("current_step", 1) >= 2:
    with st.expander("2️⃣ Role Definition", expanded=(st.session_state.get("current_step") == 2)):
        job_spec.role_description = st.text_area("Role Description *", value=job_spec.role_description or "")
        job_spec.reports_to = st.text_input("Reports To", value=job_spec.reports_to or "")
        job_spec.supervises = st.text_input("Supervises", value=job_spec.supervises or "")
        job_spec.role_type = st.selectbox("Role Type", ["", "Individual Contributor", "Manager", "Executive"], index=0 if not job_spec.role_type else None, key="role_type_select")
        job_spec.role_type = st.session_state["role_type_select"]  # reflect selectbox choice into model
        # ... more fields like role_priority_projects, travel_requirements, etc.
        if st.button("Next ➡️", key="to_step_3"):
            st.session_state["current_step"] = 3

# Section 3: Key Responsibilities (visible after Step 2) ...
if st.session_state.get("current_step", 1) >= 3:
    with st.expander("3️⃣ Key Responsibilities & Tasks", expanded=(st.session_state.get("current_step") == 3)):
        job_spec.key_responsibilities = st.text_area("Key Responsibilities *", value=job_spec.key_responsibilities or "")
        job_spec.technical_tasks = st.text_area("Technical Tasks", value=job_spec.technical_tasks or "")
        job_spec.managerial_tasks = st.text_area("Managerial Tasks", value=job_spec.managerial_tasks or "")
        # ... etc.
        if st.button("Next ➡️", key="to_step_4"):
            st.session_state["current_step"] = 4

# ... (Sections 4-7 similarly for Skills, Requirements, Compensation, etc.)

# Final Section: Summary & Confirmation (visible at last step)
if st.session_state.get("current_step", 1) >= 8:
    st.header("✅ Review & Complete")
    st.write("Please review all the information entered. You can expand the sections above to make any changes.")
    # Display a summary of all fields
    spec_dict = job_spec.model_dump()
    for field, value in spec_dict.items():
        st.markdown(f"**{field.replace('_',' ').title()}:** {value}")
    st.success("All sections completed. You may now submit the job vacancy or export it.")
