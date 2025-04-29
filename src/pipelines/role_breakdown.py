import openai
from src.models.job_models import JobSpec

SYSTEM_MSG = "You are an assistant helping to elaborate a job role definition based on given information."

def generate_role_breakdown(spec: dict) -> dict:
    """
    Use GPT to generate detailed role definition (description, reports_to, supervises, etc.)
    based on the current job spec fields (spec should be a dict possibly from SessionState.get_job_spec_dict()).
    Returns a dict of the filled fields.
    """
    # Construct a prompt using existing spec data
    job_title = spec.get("job_title") or "this role"
    company = spec.get("company_name") or ""
    industry = spec.get("industry_sector") or ""
    intro = f"The role is '{job_title}'."
    if company:
        intro += f" Company: {company}."
    if industry:
        intro += f" Industry: {industry}."
    intro += " Provide a role overview and reporting structure."
    user_msg = intro + (
        "\nPlease draft:\n"
        "- A role_description (what this role does and its purpose).\n"
        "- Who it reports_to and who it supervises (if any).\n"
        "- Key performance metrics and priority projects for this role (if known).\n"
        "Output only in JSON with keys: role_description, reports_to, supervises, role_performance_metrics, role_priority_projects."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_MSG},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.7,
            max_tokens=800
        )
        content = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"generate_role_breakdown error: {e}")
        return {}

    # Remove code fences if any and parse JSON
    if content.startswith("```"):
        content = content.strip("` \n")
    result = {}
    try:
        result = JobSpec.model_validate_json(content)  # This will ignore extra keys not in JobSpec
        result = result.model_dump()
    except Exception as e:
        # If parsing fails (maybe the model gave just the subset JSON), we attempt to safely eval or so
        try:
            import json
            partial = json.loads(content)
            # Only keep the relevant keys we expect in this stage
            allowed_keys = {"role_description", "reports_to", "supervises", "role_performance_metrics", "role_priority_projects"}
            for k, v in partial.items():
                if k in allowed_keys:
                    result[k] = v
        except Exception as e2:
            print(f"Failed to parse role_breakdown JSON: {e2}")
    return result
