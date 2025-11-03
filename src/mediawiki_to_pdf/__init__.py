import importlib.metadata
import logging
from dataclasses import dataclass
from typing import Dict, Any

mediawiki_to_pdf_logger = logging.getLogger(__name__)

__version__ = importlib.metadata.version('mediawiki-to-pdf')


@dataclass
class WikiPage:
    """Page info"""
    pageid: int
    ns: int
    title: str

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "WikiPage":
        """Create a WikiPage instance from a dict."""
        return WikiPage(
            pageid=int(data["pageid"]),
            ns=int(data["ns"]),
            title=data["title"],
        )


from mediawiki_to_pdf.wsession import MediaWikiSession
from mediawiki_to_pdf.lib import get_pages_in_category
from mediawiki_to_pdf.pdf import get_pdf_by_title, get_pdf
