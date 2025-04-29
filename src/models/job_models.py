from pydantic import BaseModel, Field
from typing import Optional, List

class JobSpec(BaseModel):
    # Basic job and company info
    job_title: str = Field(..., description="Title of the job position")
    company_name: Optional[str] = Field(None, description="Name of the company offering the job")
    brand_name: Optional[str] = Field(None, description="Brand or subsidiary name if applicable")
    headquarters_location: Optional[str] = Field(None, description="Headquarters location of the company")
    city: Optional[str] = Field(None, description="City/region of the job")
    company_website: Optional[str] = Field(None, description="Company website URL")
    company_size: Optional[str] = Field(None, description="Size of the company (e.g., number of employees or category like '100-500')")
    industry_sector: Optional[str] = Field(None, description="Industry sector of the company")
    job_type: Optional[str] = Field(None, description="Type of job (e.g., Full-time, Part-time)")
    contract_type: Optional[str] = Field(None, description="Contract type (e.g., Permanent, Temporary, Internship)")
    job_level: Optional[str] = Field(None, description="Level/seniority of the role (e.g., Entry, Manager, Director)")
    date_of_employment_start: Optional[str] = Field(None, description="Start date of employment or 'ASAP' etc.")

    # Role Definition
    role_description: Optional[str] = Field(None, description="Overview of the role's purpose and scope")
    reports_to: Optional[str] = Field(None, description="Position or title this role reports to")
    supervises: Optional[str] = Field(None, description="Positions or titles this role supervises (if any)")
    role_type: Optional[str] = Field(None, description="Type of role (e.g., Technical, Managerial, Support)")
    role_performance_metrics: Optional[str] = Field(None, description="How performance in this role is measured")
    role_priority_projects: Optional[str] = Field(None, description="Current priority projects or goals for this role")
    travel_requirements: Optional[str] = Field(None, description="Travel requirements for the role, if any")
    work_schedule: Optional[str] = Field(None, description="Work schedule (e.g., Mon-Fri, shifts) and flexibility")
    decision_making_authority: Optional[str] = Field(None, description="Decisions this role is authorized to make")
    role_keywords: Optional[str] = Field(None, description="Keywords associated with the role (for search/SEO)")

    # Tasks & Responsibilities
    task_list: Optional[List[str]] = Field(None, description="List of main tasks for the role")
    key_responsibilities: Optional[str] = Field(None, description="Summary of key responsibilities")
    technical_tasks: Optional[List[str]] = Field(None, description="Technical or hands-on tasks part of the role")
    managerial_tasks: Optional[List[str]] = Field(None, description="Managerial or leadership tasks part of the role")

    # Qualifications (if any – not sure if present in original, add if needed)
    # e.g., qualifications: Optional[str] = None, etc.

    # (We can extend with more fields like salary, benefits, publication date, etc., as needed.)

    # Enable model config for JSON serialization if needed
    model_config = {"populate_by_name": True, "str_strip_whitespace": True}
