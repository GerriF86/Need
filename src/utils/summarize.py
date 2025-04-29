import os
import openai

# Choose a model for summarization: use GPT-3.5 for economy/standard to save cost, GPT-4 for high fidelity if needed.
SUMMARIZE_MODEL_ECO = os.getenv("SUMMARIZE_MODEL_ECO", "gpt-3.5-turbo")
SUMMARIZE_MODEL_HI = os.getenv("SUMMARIZE_MODEL_HI", "gpt-4")

def summarize_text(text: str, quality: str = "standard") -> str:
    """
    Summarize the given text at the specified quality level.
    quality: "economy", "standard", or "high".
    Returns a summary of the text.
    """
    if not text:
        return ""
    # Define length/ detail based on quality
    if quality not in {"economy", "standard", "high"}:
        quality = "standard"
    if quality == "economy":
        prompt = ("Summarize the following text very briefly, focusing only on the most essential points:\n" + text)
        model = SUMMARIZE_MODEL_ECO
        max_tokens = 300
    elif quality == "high":
        prompt = ("Summarize the following text in detail, preserving as many specifics as possible. " 
                  "Your summary can be lengthy if needed:\n" + text)
        model = SUMMARIZE_MODEL_HI
        max_tokens = 1500
    else:  # standard
        prompt = ("Summarize the following text, capturing all important details but in a more concise form:\n" + text)
        model = SUMMARIZE_MODEL_ECO
        max_tokens = 600

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=max_tokens
        )
        summary = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"summarize_text: API error during summarization - {e}")
        # In case of error, fallback to simple truncation
        summary = text[:1000] + "..."
    return summary
