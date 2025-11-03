#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path

from mediawiki_to_pdf import MediaWikiSession, get_pdf_by_title, mediawiki_to_pdf_logger, get_pages_in_category, get_pdf

HTML_TO_PDF = Path('/usr/bin/wkhtmltopdf')


def main():
    logging.basicConfig()
    if not HTML_TO_PDF.is_file():
        raise ValueError(f"Install {HTML_TO_PDF.as_posix()}")

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('yaml',help="Configuration file")
    parser.add_argument('-l', '--loglevel', default='WARN', help="Python logging level")

    args = parser.parse_args()
    mediawiki_to_pdf_logger.setLevel(getattr(logging,args.loglevel))
    cfg, session = MediaWikiSession.parse_yaml(args.yaml)
    for mcat in cfg['categories']:
        mediawiki_to_pdf_logger.info(f"Category: {mcat}")
        cfg, session = MediaWikiSession.parse_yaml(args.yaml)
        for wikipage in get_pages_in_category(session,mcat):
            mediawiki_to_pdf_logger.info(f"Page {wikipage.title}")
            pdf = wikipage.title.replace(' ','-') + '.pdf'
            get_pdf(session,wikipage,pdf)



if __name__ == "__main__":
    main()

