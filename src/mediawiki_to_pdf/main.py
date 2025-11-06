#!/usr/bin/env python3
import argparse
import importlib
import logging
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from mediawiki_to_pdf import MediaWikiSession, get_pdf_by_title, mediawiki_to_pdf_logger, get_pages_in_category, \
    get_pdf, __version__

HTML_TO_PDF = Path('/usr/bin/wkhtmltopdf')


@dataclass
class ArchiveModule:
    mod: ModuleType
    data: Any


def main():
    logging.basicConfig()
    if not HTML_TO_PDF.is_file():
        raise ValueError(f"Install {HTML_TO_PDF.as_posix()}")

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('yaml', help="Configuration file")
    parser.add_argument('-l', '--loglevel', default='WARN', help="Python logging level")
    parser.add_argument('-V', '--version', action='store_true', help="Print version")
    args = parser.parse_args()
    if (args.version):
        print(__version__)
    mediawiki_to_pdf_logger.setLevel(getattr(logging, args.loglevel))
    cfg, session = MediaWikiSession.parse_yaml(args.yaml)

    # find archiver specified in configuration
    archive_modules = []
    for archive, archive_data in cfg.get('archives', {}).items():
        m = importlib.import_module(f'mediawiki_to_pdf.{archive}', archive)
        archive_modules.append(ArchiveModule(m, archive_data))

    staging = Path(cfg.get('staging folder', '.'))
    if not staging.is_dir():
        raise ValueError(f"{staging.as_posix()} is not a directory")

    for mcat in cfg.get('categories', []):
        mediawiki_to_pdf_logger.info(f"Category: {mcat}")
        cfg, session = MediaWikiSession.parse_yaml(args.yaml)
        for wikipage in get_pages_in_category(session, mcat):
            mediawiki_to_pdf_logger.info(f"Page {wikipage.title}")
            pdf = wikipage.title.replace(' ', '-') + '.pdf'
            get_pdf(session, wikipage, staging / pdf)

    for page in cfg.get('pages', []):
        pdf = page.replace('_', '-') + '.pdf'
        mediawiki_to_pdf_logger.info(f"Converting {page} to {pdf}")
        get_pdf_by_title(session, page, staging / pdf)
    files = list(staging.glob('*'))
    for am in archive_modules:
        am.mod.upload(am.data, files)


if __name__ == "__main__":
    main()
