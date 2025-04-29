# src/agents/vacancy_agent.py

import openai
from typing import Optional
from src.models.job_models import JobSpec
from src.tools.scraping_tools import scrape_company_site
from src.tools.file_tools import extract_text_from_file

# Initialize OpenAI client (API Key should be loaded from environment or secrets)
client = openai.OpenAI()

# Define our available "tools" for the Assistant
tools = [
    {
        "type": "function",
        "function": {
            "name": "scrape_company_site",
            "description": "Fetch basic company info (title and meta description) from a company website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL of the company homepage."}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_text_from_file",
            "description": "Extract readable text from uploaded PDF, DOCX, or TXT file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_content": {"type": "string", "description": "Base64-encoded file content."},
                    "filename": {"type": "string", "description": "Original filename with extension."}
                },
                "required": ["file_content", "filename"]
            }
        }
    }
]

# System prompt for the Assistant
SYSTEM_MESSAGE = (
    "You are Vacalyser, an AI recruitment assistant. "
    "You help extract detailed structured job vacancy information from text, websites, or files. "
    "Your goal is to return complete and correct JSON according to the JobSpec model."
)

def auto_fill_job_spec(input_url: str = "", file_bytes: bytes = None, file_name: str = "") -> dict:
    """
    Analyze a job description via URL or file upload, return extracted fields as a dictionary.
    """

    # Build the user message
    user_message = ""
    if input_url:
        user_message += f"The job ad is located at this URL: {input_url}\n"
    if file_bytes:
        user_message += "A job ad file is uploaded. Please analyze its contents carefully.\n"
    if not user_message:
        raise ValueError("You must provide either a URL or a file.")

    user_message += "Please extract all job information and return it in a JSON format matching the JobSpec schema."

    # Launch a temporary Assistant
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": user_message}
        ],
        tools=tools,
        tool_choice="auto",  # Let the model decide which tool to call
        max_tokens=1500
    )

    content = response.choices[0].message.content
    if not content:
        return {}

    try:
        data = JobSpec.model_validate_json(content)
        return data.model_dump()
    except Exception as e:
        print(f"Vacancy agent returned invalid JSON: {e}")
        return {}

