"""Citation management for structured source tracking and bibliography generation."""
import logging
from typing import List, Dict
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)


class CitationManager:
    """Manages source citations throughout the research pipeline.
    
    Collects sources from the Researcher agent, assigns numbered references,
    and generates formatted bibliography sections for reports.
    """

    def __init__(self):
        self._sources: List[Dict[str, str]] = []
        self._url_index: Dict[str, int] = {}  # url -> reference number

    @property
    def sources(self) -> List[Dict[str, str]]:
        """All collected sources."""
        return self._sources

    @property
    def count(self) -> int:
        """Number of unique sources."""
        return len(self._sources)

    def add_source(self, title: str, url: str, snippet: str = "") -> int:
        """Add a source and return its reference number.
        
        Deduplicates by URL. Returns existing reference number if URL already tracked.
        """
        if not url or not url.startswith("http"):
            return -1

        # Deduplicate by URL
        if url in self._url_index:
            return self._url_index[url]

        ref_num = len(self._sources) + 1
        domain = urlparse(url).netloc.replace("www.", "")

        source = {
            "ref_num": str(ref_num),
            "title": title.strip() if title else "Untitled",
            "url": url.strip(),
            "snippet": snippet[:200] if snippet else "",
            "domain": domain,
            "accessed_date": datetime.now().strftime("%Y-%m-%d")
        }

        self._sources.append(source)
        self._url_index[url] = ref_num
        logger.info(f"Added source [{ref_num}]: {title[:50]}")
        return ref_num

    def add_sources_from_search(self, search_results: List[Dict]) -> List[int]:
        """Add multiple sources from search results. Returns list of reference numbers."""
        ref_nums = []
        for result in search_results:
            ref = self.add_source(
                title=result.get("title", "Untitled"),
                url=result.get("link", ""),
                snippet=result.get("snippet", "")
            )
            if ref > 0:
                ref_nums.append(ref)
        return ref_nums

    def format_sources_for_prompt(self) -> str:
        """Format all sources as a numbered list for the Writer prompt."""
        if not self._sources:
            return "No sources available."

        lines = []
        for src in self._sources:
            lines.append(
                f"[{src['ref_num']}] {src['title']} — {src['domain']} ({src['url']})"
            )
        return "\n".join(lines)

    def format_bibliography(self) -> str:
        """Generate a formatted References/Bibliography section for the final report."""
        if not self._sources:
            return ""

        lines = ["\n---\n\n## References\n"]
        for src in self._sources:
            line = f"[{src['ref_num']}] "
            line += f"**{src['title']}**"
            if src.get('domain'):
                line += f" — *{src['domain']}*"
            if src.get('url'):
                line += f" — [{src['url']}]({src['url']})"
            line += f" (Accessed: {src.get('accessed_date', 'N/A')})"
            lines.append(line)

        return "\n\n".join(lines)

    def to_list(self) -> List[Dict[str, str]]:
        """Export sources as a list of dicts for database storage."""
        return self._sources.copy()

    @classmethod
    def from_list(cls, sources: List[Dict[str, str]]) -> 'CitationManager':
        """Reconstruct a CitationManager from a stored list of sources."""
        manager = cls()
        for src in sources:
            manager.add_source(
                title=src.get("title", "Untitled"),
                url=src.get("url", ""),
                snippet=src.get("snippet", "")
            )
        return manager
