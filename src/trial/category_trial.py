#!/usr/bin/env python3
import argparse
import logging

from mediawiki_to_pdf import MediaWikiSession, get_pages_in_category, mediawiki_to_pdf_logger

_logger = logging.getLogger(__name__)


def main():
    logging.basicConfig()
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-l', '--loglevel', default='WARN', help="Python logging level")

    args = parser.parse_args()
    mediawiki_to_pdf_logger.setLevel(getattr(logging,args.loglevel))
    cfg, session = MediaWikiSession.parse_yaml('category.yaml')
    cat = cfg['category']
    pages = get_pages_in_category(session,cat)
    print(len(pages))

        


if __name__ == "__main__":
    main()
