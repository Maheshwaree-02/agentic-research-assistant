from duckduckgo_search import DDGS
from typing import List, Dict
from ddgs import DDGS
def web_search(query: str, max_results: int = 5) -> List[Dict]:
    """Perform web search using DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [{
                "title": r.get("title", "No Title"),
                "snippet": r.get("body", ""),
                "link": r.get("href", "")
            } for r in results]
    except Exception as e:
        return [{"title": "Search Error", "snippet": str(e), "link": ""}]

def browse_page(url: str) -> str:
    """Simple page content fetcher"""
    import requests
    from bs4 import BeautifulSoup
    
    try:
        headers = {"User-Agent": "ResearchPilot/1.0"}
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text[:8000]  # Limit for token safety
    except Exception as e:
        return f"Failed to fetch page {url}: {str(e)}"