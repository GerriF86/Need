from openai_agents import tool

@tool
def scrape_company_site(url: str) -> dict:
    """Fetch a webpage and return basic info like title and meta description."""
    import requests
    from bs4 import BeautifulSoup
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.title.string if soup.title else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag["content"] if desc_tag else ""
    return {"site_title": title, "site_description": description}
