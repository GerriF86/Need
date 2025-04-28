from openai_agents import OpenAIAgent, AgentException
from openai_agents.tools import PythonAgentToolset
from src.tools.scraping_tools import scrape_company_site
from src.tools.file_tools import extract_text_from_file
from src.models.job_models import JobSpec

# Define an OpenAI-based agent with GPT-4 and our tools
tools = [scrape_company_site, extract_text_from_file]
toolset = PythonAgentToolset(tools=tools)
agent = OpenAIAgent(
    model="gpt-4-0613",  # using a GPT-4 model that supports function calling
    tools=toolset,
    system_message=("You are Vacalyser, an AI agent that helps fill out job vacancy details. "
                    "You have access to tools for web scraping and file parsing. "
                    "Your goal is to extract or infer all relevant job fields in JSON format. "
                    "If given a URL or file, use the appropriate tool to get content. "
                    "Then analyze the content and map to known fields. "
                    "Finally, output a JSON matching the JobSpec model schema.")
    # We will add guardrails and tracing below
)

# Optional: Enable tracing for this agent (logs to OpenAI tracing system or local trace viewer)
agent.enable_tracing()  # This will record each tool use and model step for debugging

# Define a function to run the agent for filling the job spec
def auto_fill_job_spec(input_url: str = "", file_bytes: bytes = None, file_name: str = "") -> dict:
    """
    Use the agent to automatically fill job spec fields from a URL or uploaded file.
    Returns a dictionary of extracted fields that can be merged into the session state or JobSpec.
    """
    # Construct the user prompt based on provided inputs
    user_prompt = ""
    if input_url:
        user_prompt += f"The job description is available at the following URL: {input_url}\n"
    if file_bytes:
        user_prompt += "An uploaded job ad file is provided. Please extract its text and details.\n"
    if not user_prompt:
        raise ValueError("No input source provided for analysis.")
    user_prompt += "Extract all possible job details and provide them in JSON format."
    try:
        result = agent.run(user_prompt)
    except AgentException as e:
        # If the agent fails or cannot parse, log error and return empty dict
        print(f"Agent error during auto-fill: {e}")
        return {}
    # If agent returns a string, attempt to parse JSON
    content = result if isinstance(result, str) else str(result)
    try:
        data = JobSpec.model_validate_json(content)
        return data.model_dump()  # Convert Pydantic model to plain dict
    except Exception:
        # If JSON parsing fails, return raw text or empty dict
        print("Agent returned non-JSON or invalid format.")
        return {}
