import argparse
import sys

from stui.stui import StuiApp
from stui import __version__


def parse_args():
    parser = argparse.ArgumentParser(description="stui")

    parser.add_argument(
        "--ssh",
        default=None,
        help="Remote destination where slurm controller is running. Format: --remote {Host name defined in ssh config} or --remote {username@server}. Does _not_ prompt for password and relies on ssh-keys for authentication.",
    )

    parser.add_argument(
        "-r",
        "--refresh-interval",
        type=int,
        default=1,
        help="Refresh interval (in seconds) for fetching data from the cluster. (Default: 1s)",
    )

    parser.add_argument(
        "-v", "--version", help="Show version and exit.", action="store_true",
    )

    args = parser.parse_args()

    return args


def cli():
    args = parse_args()

    if args.version:
        print(__version__)
        sys.exit()

    StuiApp(args).run()


if __name__ == "__main__":
    cli()
