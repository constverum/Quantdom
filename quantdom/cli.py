"""CLI."""

import argparse
import logging
import sys

from . import __version__ as version
from .app import main


def create_parser():
    parser = argparse.ArgumentParser(
        prog='quantdom',
        add_help=False,
        description='''
            Quantdom is a simple but powerful backtesting framework,
            that strives to let you focus on modeling financial strategies,
            portfolio management, and analyzing backtests.''',
        epilog='''Run '%(prog)s <command> --help'
                  for more information on a command.
                  Suggestions and bug reports are greatly appreciated:
                  https://github.com/constverum/Quantdom/issues''',
    )
    parser.add_argument(
        '--debug', action='store_true', help='Run in debug mode'
    )
    parser.add_argument(
        '--log',
        nargs='?',
        default=logging.CRITICAL,
        choices=['NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level',
    )
    parser.add_argument(
        '--version',
        '-v',
        action='version',
        version='%(prog)s {v}'.format(v=version),
        help='Show program\'s version number and exit',
    )
    parser.add_argument(
        '--help', '-h', action='help', help='Show this help message and exit'
    )
    return parser


def cli(args=sys.argv[1:]):
    parser = create_parser()
    ns = parser.parse_args(args)

    if ns.debug:
        ns.log = logging.DEBUG

    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        datefmt='[%H:%M:%S]',
        level=ns.log,
    )

    main(debug=ns.debug)
