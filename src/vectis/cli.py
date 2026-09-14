"""VECTIS command-line interface."""

from __future__ import annotations

import argparse

from vectis import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vectis",
        description="VECTIS language toolchain",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="display the VECTIS version",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        print(__version__)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
