#!/usr/bin/env python3

import argparse
import sys

from commands.push_file import run_push_file
from commands.pull_file import run_pull_file
from commands.push_folder import run_push_folder
from commands.pull_folder import run_pull_folder


def main():

    parser = argparse.ArgumentParser(
        description="HPC Transfer Tool"
    )

    sub = parser.add_subparsers(dest="command")

    push_file = sub.add_parser("push-file")
    push_file.add_argument("--file", required=True)
    push_file.add_argument("--config", required=True)

    pull_file = sub.add_parser("pull-file")
    pull_file.add_argument("--file", required=True)
    pull_file.add_argument("--config", required=True)

    push_folder = sub.add_parser("push-folder")
    push_folder.add_argument("--folder", required=True)
    push_folder.add_argument("--config", required=True)
    push_folder.add_argument("--workers", type=int)

    pull_folder = sub.add_parser("pull-folder")
    pull_folder.add_argument("--folder", required=True)
    pull_folder.add_argument("--config", required=True)

    args = parser.parse_args()

    if args.command == "push-file":
        run_push_file(args)

    elif args.command == "pull-file":
        run_pull_file(args)

    elif args.command == "push-folder":
        run_push_folder(args)

    elif args.command == "pull-folder":
        run_pull_folder(args)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
