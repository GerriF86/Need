from pydantic import BaseModel, Field, HttpUrl, conint, validator
from datetime import date, datetime

class JobSpec(BaseModel):
    job_title: str = Field(..., title="Job Title")
    company_name: str = Field(..., title="Company Name")
    brand_name: str = Field("", title="Brand Name (if different)")
    headquarters_location: str = Field("", title="Headquarters Location")
    company_website: HttpUrl | None = Field(None, title="Company Website")
    date_of_employment_start: str = Field("", title="Employment Start Date (e.g. ASAP or YYYY-MM)")
    job_type: str = Field("", title="Job Type")  # Could use Literal choices for limited options
    contract_type: str = Field("", title="Contract Type")
    job_level: str = Field("", title="Job Level")
    city: str = Field("", title="City")
    team_structure: str = Field("", title="Team Structure")
    role_description: str = Field("", title="Role Description")
    reports_to: str = Field("", title="Reports To")
    supervises: str = Field("", title="Supervises")
    role_type: str = Field("", title="Role Type")
    # ... (and so on for all fields in the session state)
    salary_range: tuple[int, int] | None = Field(None, title="Salary Range (min, max)")
    currency: str = Field("", title="Salary Currency")
    # etc. for remaining fields...
    
    # Example validator: ensure salary range makes sense if provided
    @validator("salary_range")
    def check_salary_range(cls, val):
        if val is not None:
            min_sal, max_sal = val
            assert min_sal <= max_sal, "Min salary must be <= max salary"
        return val
