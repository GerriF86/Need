import os
from typing import Optional, Dict, Any

# Import Pydantic model
from src.models.job_models import JobSpec

# Import tool functions
from src.tools.scraping_tools import scrape_company_site
from src.tools.file_tools import extract_text_from_file

# Import summarization utility
from src.utils.summarize import summarize_text

# Determine runtime mode (OpenAI vs LocalAI) via env or config
USE_LOCAL_MODEL = os.getenv("VACALYSER_LOCAL_MODE", "0") == "1"

# If using local model, import or configure it (e.g., via Ollama API client)
if USE_LOCAL_MODEL:
    from src.local.local_client import LocalLLMClient
    local_client = LocalLLMClient(model_name="llama3.2-3b")  # example local model

# Initialize OpenAI client for API usage (ensure API key is set in environment)
openai_client = None
if not USE_LOCAL_MODEL:
    import openai
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define the tool specifications for OpenAI function calling
TOOLS = [
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
            "description": "Extract readable text from an uploaded job-ad file (PDF, DOCX, or TXT).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_content": {"type": "string", "description": "Base64-encoded file content."},
                    "filename":    {"type": "string", "description": "Original filename with extension."}
                },
                "required": ["file_content", "filename"]
            }
        }
    }
    # (Note: In OpenAI’s Python SDK, we could alternatively pass actual function objects via function_call parameter,
    # but here we keep the explicit schema definition for clarity.)
]

# System role prompt defining the assistant’s identity and task
SYSTEM_MESSAGE = (
    "You are Vacalyser, an AI assistant for recruiters. "
    "Your job is to extract detailed, structured job vacancy information from input text (job ads) or websites. "
    "Return the information as JSON that matches the schema of the JobSpec model, with no extra commentary."
)

def auto_fill_job_spec(input_url: str = "", file_bytes: bytes = None, file_name: str = "", summary_quality: str = "standard") -> Dict[str, Any]:
    """
    Analyze a job description from a URL or file and return extracted fields as a dictionary.
    - input_url: URL of a job advertisement webpage.
    - file_bytes: Raw bytes of an uploaded job description file.
    - file_name: Filename of the uploaded file.
    - summary_quality: One of {"economy", "standard", "high"} indicating how much to compress the content if it's large.
    """
    # Validate input
    if not input_url and not file_bytes:
        raise ValueError("auto_fill_job_spec requires either a URL or a file input.")
    if input_url and file_bytes:
        # If both are provided, we prioritize URL and ignore the file to avoid confusion.
        file_bytes = None
        file_name = ""

    # Prepare the user message content
    user_message = ""
    if input_url:
        user_message += f"The job ad is located at this URL: {input_url}\n"
    if file_bytes:
        user_message += "A job ad file is provided. Please analyze its contents carefully.\n"
    user_message += "Extract all relevant job information and return it in JSON format matching the JobSpec schema."

    # If the input text might be very long, consider summarizing it to compress context
    # (We perform summarization outside the model to conserve tokens in the prompt if needed)
    if file_bytes and file_name:
        # If it's a file, we can attempt to compress if the text is huge.
        try:
            text_length = len(file_bytes)
        except Exception:
            text_length = 0
        # Heuristics: if file size > 100KB, do summarization depending on quality
        if text_length > 100_000:  # ~100 KB
            extracted_text = extract_text_from_file(file_content=file_bytes.decode('utf-8', errors='ignore'), filename=file_name)
            if isinstance(extracted_text, str) and len(extracted_text) > 5000:  # if extracted text is large
                summary = summarize_text(extracted_text, quality=summary_quality)
                # Replace user instruction to refer to summary instead of full text
                user_message = (
                    "The job ad text was summarized due to length. Please extract job info from the following summary:\n"
                    f"{summary}\nReturn the info as JSON per JobSpec."
                )
    # (For URL content, the model will call scrape_company_site itself if needed, we handle large content in the tool itself if required.)

    if USE_LOCAL_MODEL:
        # Local model mode: we cannot rely on the model to call functions. So we handle URL/file upfront.
        if input_url:
            try:
                site_info = scrape_company_site(url=input_url)
                # Append any info from site to the user_message to assist local model
                if site_info.get("title") or site_info.get("description"):
                    user_message += "\n"
                    user_message += f"(Website summary: {site_info.get('title','')}: {site_info.get('description','')})"
            except Exception as e:
                # Log scraping error, but continue without it
                user_message += f"\n(Note: Could not scrape site: {e})"
        if file_bytes and file_name:
            try:
                text = extract_text_from_file(file_content=file_bytes.decode('utf-8', errors='ignore'), filename=file_name)
                if text and isinstance(text, str):
                    # Possibly summarize if too long
                    if len(text) > 5000:
                        text = summarize_text(text, quality=summary_quality)
                    user_message += "\nFile content:\n" + text[:10000]  # include at most 10000 chars of text or summary
                else:
                    user_message += "\n(Note: No extractable text from file.)"
            except Exception as e:
                user_message += f"\n(Note: Could not extract file text: {e})"
        # Query local LLM with the constructed user_message
        try:
            response_text = local_client.generate(text=user_message, system=SYSTEM_MESSAGE)
        except Exception as e:
            print(f"Local model generation failed: {e}")
            return {}
        content = response_text
    else:
        # OpenAI API mode
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4-0613",  # using function-calling enabled model variant
                messages=[
                    {"role": "system", "content": SYSTEM_MESSAGE},
                    {"role": "user", "content": user_message}
                ],
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=1500
            )
        except Exception as api_error:
            print(f"OpenAI API error in auto_fill_job_spec: {api_error}")
            return {}
        # The response could contain either a direct answer or tool calls. The OpenAI SDK should handle tool execution automatically.
        # We assume final response is in response.choices[0].message (after any function calls).
        try:
            content = response.choices[0].message.content
        except Exception as e:
            print(f"Unexpected response structure: {e}")
            return {}
        if not content:
            # If the assistant didn't return a message (possibly only function calls happened), try to gather from tool calls
            # This scenario is unlikely with tool_choice='auto', as final answer should be present.
            content = ""
            if hasattr(response, 'choices') and len(response.choices) > 0:
                # Check if a tool_call was made and no final content yet
                # (In openai.FunctionCalling, final content might be in a tool call result)
                try:
                    tool_calls = response.choices[0].finish_reason  # not exactly, but conceptual
                except:
                    tool_calls = None
                # If tool_calls were present without final content, we might need to compose final content.
                # For simplicity, we handle this by returning what we have.
                content = str(tool_calls) or ""
            if not content:
                return {}

    # Now 'content' should be a JSON string from the assistant.
    # Validate and parse it using Pydantic
    content_str = content.strip()
    if content_str.startswith("```"):  # remove any markdown formatting if present
        content_str = content_str.strip("``` \n")
    if content_str == "":
        return {}
    try:
        job_spec = JobSpec.model_validate_json(content_str)
    except Exception as e:
        print(f"Vacancy agent returned invalid JSON. Error: {e}")
        # Attempt a second-chance fix: if content is almost JSON but not quite
        # (We could implement a quick fix like adding missing quotes or wrapping it, but that's complex. Instead, we retry the model.)
        if not USE_LOCAL_MODEL and openai_client:
            repair_system_msg = "Your previous output was not valid JSON. Only output a valid JSON matching JobSpec now."
            try:
                repair_resp = openai_client.chat.completions.create(
                    model="gpt-4-0613",
                    messages=[
                        {"role": "system", "content": SYSTEM_MESSAGE},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": content_str},
                        {"role": "system", "content": repair_system_msg}
                    ],
                    tools=[],
                    temperature=0,
                    max_tokens=1200
                )
                content_fixed = repair_resp.choices[0].message.content.strip()
                job_spec = JobSpec.model_validate_json(content_fixed)
                print("Successfully got valid JSON on retry.")
            except Exception as e2:
                print(f"Retry also failed: {e2}")
                return {}
        else:
            return {}
    # Convert to dictionary (Pydantic model -> dict)
    return job_spec.model_dump()
