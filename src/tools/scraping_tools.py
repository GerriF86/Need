import requests
from bs4 import BeautifulSoup

def scrape_company_site(url: str) -> dict:
    """
    Fetch basic company info from a website URL.
    Returns a dict with 'title' and 'description' of the page, if found.
    """
    result = {"title": None, "description": None}
    if not url:
        return result
    try:
        # Ensure URL has scheme
        if not url.startswith("http"):
            url = "https://" + url
        # Make request with timeout
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        # In case of any request error, just return empty info
        print(f"scrape_company_site: Failed to fetch {url} - {e}")
        return result

    # Parse HTML content
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"scrape_company_site: HTML parse error for {url} - {e}")
        return result

    # Extract page title
    title_tag = soup.find("title")
    if title_tag and title_tag.text:
        # Clean title text
        result["title"] = title_tag.text.strip()

    # Extract meta description
    desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"name": "Description"})
    if desc_tag:
        content = desc_tag.get("content", "")
        if content:
            result["description"] = content.strip()

    # If description not found in meta, try first paragraph as fallback
    if not result["description"]:
        p_tag = soup.find("p")
        if p_tag:
            text = p_tag.get_text(" ", strip=True)
            # Limit length to avoid very long text
            if text:
                result["description"] = (text[:200] + "...") if len(text) > 200 else text

    # Truncate overly long description for safety (shouldn't normally happen with above logic)
    if result["description"] and len(result["description"]) > 300:
        result["description"] = result["description"][:300] + "..."

    return result
