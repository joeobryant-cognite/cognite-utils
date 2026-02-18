#!/usr/bin/env python3
"""
Command-line entry point for exporting Cognite groups to Excel.
Run from the project root: poetry run python export_groups.py [options]
"""
import argparse
import sys
from pathlib import Path

# Allow importing from utils when run from project root
_utils = Path(__file__).resolve().parent / "utils"
if str(_utils) not in sys.path:
    sys.path.insert(0, str(_utils))

from cognite_groups_export import export_groups


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export Cognite IAM groups to an Excel file (device-code auth, no local port)."
    )
    parser.add_argument(
        "-c",
        "--customers",
        metavar="NAME",
        nargs="*",
        default=None,
        help="Customer(s) to export (from cognite_auth_config.json). Default: all.",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        default="groups_by_customer.xlsx",
        help="Output Excel file path (default: groups_by_customer.xlsx)",
    )
    parser.add_argument(
        "--token-cache-dir",
        metavar="DIR",
        default=None,
        help="Directory for token cache files (default: ~/.cognite/token_cache)",
    )
    parser.add_argument(
        "--no-profile",
        action="store_true",
        help="Do not print user profile for each customer",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Less output",
    )
    args = parser.parse_args()

    customers = args.customers
    if customers is not None and len(customers) == 0:
        customers = None  # no args => all customers

    token_cache_dir = Path(args.token_cache_dir) if args.token_cache_dir else None

    export_groups(
        customers=customers,
        output_file=Path(args.output),
        token_cache_dir=token_cache_dir,
        show_profile=not args.no_profile,
        show_raw_capabilities=False,
        max_groups_preview=3,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
