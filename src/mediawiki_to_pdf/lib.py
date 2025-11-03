import logging
from typing import Iterable

from mediawiki_to_pdf import MediaWikiSession, mediawiki_to_pdf_logger, WikiPage


def get_pages_in_category(session: MediaWikiSession, category: str) -> Iterable[WikiPage]:
    """Search a category"""
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": "max",  # up to 500 for normal users, 5000 for bots
        "format": "json"
    }

    pages = []

    while True:
        r = session.get(session.apiurl, params=params)
        r.raise_for_status()
        data = r.json()
        pages.extend(data["query"]["categorymembers"])

        # handle continuation if there are more results
        if "continue" in data:
            params.update(data["continue"])
        else:
            break
    if mediawiki_to_pdf_logger.isEnabledFor(logging.INFO):
        for p in pages:
            mediawiki_to_pdf_logger.info(p)
    return [WikiPage.from_dict(p) for p in pages]
