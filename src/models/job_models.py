# src/models/job_models.py

from pydantic import BaseModel, Field, HttpUrl, conint, validator
from typing import Optional, List, Tuple
from datetime import date

class JobSpec(BaseModel):
    # Discovery
    job_title: str = Field(..., title="Job Title")
    input_url: Optional[HttpUrl] = Field(None, title="Job Ad URL")
    parsed_data_raw: Optional[str] = Field("", title="Raw Parsed Data")
    source_language: Optional[str] = Field("", title="Source Language")

    # Company Information
    company_name: str = Field(..., title="Company Name")
    brand_name: Optional[str] = Field("", title="Brand Name (if different)")
    headquarters_location: Optional[str] = Field("", title="Headquarters Location")
    company_website: Optional[HttpUrl] = Field(None, title="Company Website")
    company_size: Optional[str] = Field("", title="Company Size")
    industry_sector: Optional[str] = Field("", title="Industry Sector")
    city: Optional[str] = Field("", title="City (Job Location)")

    # Job Basics
    job_type: str = Field(..., title="Job Type")
    contract_type: str = Field(..., title="Contract Type")
    job_level: str = Field(..., title="Job Level")
    date_of_employment_start: Optional[str] = Field("", title="Start Date")

    # Role Description
    role_description: str = Field(..., title="Role Description")
    reports_to: Optional[str] = Field("", title="Reports To")
    supervises: Optional[str] = Field("", title="Supervises")
    role_type: Optional[str] = Field("", title="Role Type")
    role_priority_projects: Optional[str] = Field("", title="Priority Projects")
    travel_requirements: Optional[str] = Field("", title="Travel Requirements")
    work_schedule: Optional[str] = Field("", title="Work Schedule")
    role_keywords: Optional[str] = Field("", title="Role Keywords")
    decision_making_authority: Optional[str] = Field("", title="Decision Making Authority")
    role_performance_metrics: Optional[str] = Field("", title="Performance Metrics")

    # Tasks
    task_list: Optional[str] = Field("", title="General Task List")
    key_responsibilities: Optional[str] = Field("", title="Key Responsibilities")
    technical_tasks: Optional[str] = Field("", title="Technical Tasks")
    managerial_tasks: Optional[str] = Field("", title="Managerial Tasks")
    administrative_tasks: Optional[str] = Field("", title="Administrative Tasks")
    customer_facing_tasks: Optional[str] = Field("", title="Customer Facing Tasks")
    internal_reporting_tasks: Optional[str] = Field("", title="Internal Reporting Tasks")
    performance_tasks: Optional[str] = Field("", title="Performance-Related Tasks")
    innovation_tasks: Optional[str] = Field("", title="Innovation Tasks")
    task_prioritization: Optional[str] = Field("", title="Task Prioritization")

    # Skills & Competencies
    must_have_skills: Optional[str] = Field("", title="Must-Have Skills")
    hard_skills: Optional[str] = Field("", title="Hard Skills")
    nice_to_have_skills: Optional[str] = Field("", title="Nice-to-Have Skills")
    soft_skills: Optional[str] = Field("", title="Soft Skills")
    certifications_required: Optional[str] = Field("", title="Certifications Required")
    language_requirements: Optional[str] = Field("", title="Language Requirements")
    tool_proficiency: Optional[str] = Field("", title="Tool Proficiency")
    domain_expertise: Optional[str] = Field("", title="Domain Expertise")
    leadership_competencies: Optional[str] = Field("", title="Leadership Competencies")
    technical_stack: Optional[str] = Field("", title="Technical Stack")
    industry_experience: Optional[str] = Field("", title="Industry Experience")
    analytical_skills: Optional[str] = Field("", title="Analytical Skills")
    communication_skills: Optional[str] = Field("", title="Communication Skills")
    project_management_skills: Optional[str] = Field("", title="Project Management Skills")
    soft_requirement_details: Optional[str] = Field("", title="Additional Soft Requirements")
    visa_sponsorship: Optional[str] = Field("", title="Visa Sponsorship")

    # Compensation
    salary_range: Optional[Tuple[int, int]] = Field(None, title="Salary Range (min, max)")
    currency: str = Field("", title="Currency")
    pay_frequency: str = Field("", title="Pay Frequency")
    bonus_scheme: Optional[str] = Field("", title="Bonus Scheme")
    commission_structure: Optional[str] = Field("", title="Commission Structure")
    vacation_days: Optional[int] = Field(28, title="Vacation Days")
    flexible_hours: Optional[str] = Field("", title="Flexible Hours")
    remote_work_policy: str = Field("", title="Remote Work Policy")
    relocation_assistance: Optional[str] = Field("", title="Relocation Assistance")
    childcare_support: Optional[str] = Field("", title="Childcare Support")

    # Recruitment
    recruitment_steps: Optional[str] = Field("", title="Recruitment Steps")
    number_of_interviews: Optional[int] = Field(2, title="Number of Interview Rounds")
    interview_format: Optional[str] = Field("", title="Interview Format")
    assessment_tests: Optional[str] = Field("", title="Assessment Tests")
    recruitment_timeline: Optional[str] = Field("", title="Recruitment Timeline (weeks)")
    onboarding_process_overview: Optional[str] = Field("", title="Onboarding Overview")
    recruitment_contact_email: Optional[str] = Field("", title="Recruitment Contact Email")
    recruitment_contact_phone: Optional[str] = Field("", title="Recruitment Contact Phone")
    application_instructions: Optional[str] = Field("", title="Application Instructions")

    # Additional Metadata
    language_of_ad: str = Field("", title="Language of Advertisement")
    translation_required: bool = Field(False, title="Translation Required")
    desired_publication_channels: Optional[str] = Field("", title="Publication Channels")
    employer_branding_elements: Optional[str] = Field("", title="Employer Branding Elements")
    internal_job_id: Optional[str] = Field("", title="Internal Job ID")
    ad_seniority_tone: str = Field("", title="Ad Seniority Tone")
    ad_length_preference: str = Field("", title="Ad Length Preference")
    deadline_urgency: Optional[str] = Field("", title="Application Deadline Urgency")
    company_awards: Optional[str] = Field("", title="Company Awards")
    diversity_inclusion_statement: Optional[str] = Field("", title="Diversity and Inclusion Statement")
    legal_disclaimers: Optional[str] = Field("", title="Legal Disclaimers")
    social_media_links: Optional[str] = Field("", title="Social Media Links")
    video_introduction_option: Optional[str] = Field("", title="Video Introduction Option")
    comments_internal: Optional[str] = Field("", title="Internal Comments")

    # Validators
    @validator("salary_range")
    def check_salary_range(cls, val):
        if val is not None:
            min_sal, max_sal = val
            if min_sal > max_sal:
                raise ValueError("Minimum salary must be less than or equal to maximum salary.")
        return val
