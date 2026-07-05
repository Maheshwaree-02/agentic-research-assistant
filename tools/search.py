"""Web search and page browsing tools."""
import time
import hashlib
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# In-memory search cache (TTL-based)
_search_cache: Dict[str, dict] = {}
_CACHE_TTL = 600  # 10 minutes


def _get_cached(key: str):
    """Get cached result if still valid."""
    if key in _search_cache:
        entry = _search_cache[key]
        if time.time() - entry["timestamp"] < _CACHE_TTL:
            return entry["data"]
        del _search_cache[key]
    return None


def _set_cache(key: str, data):
    """Store result in cache."""
    _search_cache[key] = {"data": data, "timestamp": time.time()}


def web_search(query: str, max_results: int = 5) -> List[Dict]:
    """Perform web search using DuckDuckGo with caching and retry."""
    cache_key = hashlib.md5(f"{query}:{max_results}".encode()).hexdigest()
    cached = _get_cached(cache_key)
    if cached:
        logger.info(f"Search cache hit for: {query[:50]}")
        return cached

    from ddgs import DDGS

    for attempt in range(3):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                formatted = [{
                    "title": r.get("title", "No Title"),
                    "snippet": r.get("body", ""),
                    "link": r.get("href", "")
                } for r in results]
                _set_cache(cache_key, formatted)
                return formatted
        except Exception as e:
            logger.warning(f"Search attempt {attempt + 1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)

    return [{"title": "Search Error", "snippet": "All search attempts failed", "link": ""}]


def browse_page(url: str) -> str:
    """Fetch and extract text content from a web page."""
    import requests
    from bs4 import BeautifulSoup

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text[:8000]
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return f"Failed to fetch page: {str(e)}"