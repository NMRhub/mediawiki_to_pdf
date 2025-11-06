import logging
import tempfile
from pathlib import Path

import pdfkit

from mediawiki_to_pdf import WikiPage, MediaWikiSession, mediawiki_to_pdf_logger


def _save_pdf_from_authenticated_session(session: MediaWikiSession, key: str, value: str, output_path: Path) -> Path:
    """
    Fetch a MediaWiki page via API and convert it to PDF using pdfkit. Return output.
    """
    # Here’s what each of those MediaWiki API query parameters does:
    #  action=parse
    #  Tells the API you want to parse page content. Instead of returning the raw wikitext,
    #  it processes it (resolving templates, formatting, etc.) into HTML or other specified formats.
    # prop=text
    #  Specifies which part(s) of the parsed output you want returned.
    #  text means: return the rendered HTML of the page (or section) after parsing.
    # format=json
    #  Sets the output format to JSON.
    #  Without this, the default output format might be XML; JSON is more convenient for most applications.
    response = session.get(
        f"{session.apiurl}?action=parse&prop=text&format=json&{key}={value}"
    )
    response.raise_for_status()
    jdata = response.json()['parse']
    html = jdata["text"]["*"]  # Full rendered HTML body
    page_title = jdata['title']

    # Wrap in basic HTML structure so wkhtmltopdf doesn’t choke
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{page_title}</title>
    </head>
    <body>
        {html}
    </body>
    </html>
    """

    # Save to temp file and convert to PDF
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as tmp_html:
        tmp_html.write(full_html)
        tmp_html.flush()
        verbose = mediawiki_to_pdf_logger.isEnabledFor(logging.DEBUG)
        pdfkit.from_file(tmp_html.name, output_path.as_posix(), verbose=verbose)

    if (rval := Path(output_path)).is_file():
        return rval
    raise RuntimeError(f"pdkfit did not generate {rval.as_posix()} from {tmp_html.name}")


def get_pdf(session: MediaWikiSession, wpage: WikiPage, output_path: Path) -> Path:
    """Get PDF by a WikiPage object"""
    return _save_pdf_from_authenticated_session(session, 'pageid', wpage.pageid, output_path)


def get_pdf_by_title(session: MediaWikiSession, page_title: str, output_path: Path) -> Path:
    """Get a PDF by title"""
    return _save_pdf_from_authenticated_session(session, 'page', page_title, output_path)
