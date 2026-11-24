# SPDX-License-Identifier: Apache-2.0 OR MIT
"""``west ppk2``: capture with ppk2-lib, then report on the marked channels.

``list``, ``capture``, ``run`` and ``power`` are the commands of ppk2-lib.
``attribute``, ``plot`` and ``budget`` run the scripts of this module.
The first two name the channels from the image of the build.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from shutil import which

from west.commands import WestCommand

SCRIPTS = Path(__file__).resolve().parents[1]
FROM_PPK2_LIB = ("list", "capture", "run", "power")
OURS = {"attribute": "attribute.py", "plot": "plot.py", "budget": "check_budget.py"}


class Ppk2(WestCommand):
    def __init__(self):
        super().__init__(
            "ppk2",
            "capture with a PPK2 and report on the marked channels",
            __doc__,
            accepts_unknown_args=True,
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(
            self.name,
            help=self.help,
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument("sub", choices=(*FROM_PPK2_LIB, *OURS))
        parser.add_argument("--build-dir", default="build", help="where zephyr.elf is")
        parser.add_argument("args", nargs=argparse.REMAINDER)
        return parser

    def do_run(self, args, unknown_args):
        rest = [*unknown_args, *args.args]
        if args.sub in FROM_PPK2_LIB:
            cli = which("ppk2")
            if cli is None:
                self.die("ppk2 not found: pip install ppk2-lib")
            sys.exit(subprocess.call([cli, args.sub, *rest]))

        # --build-dir is accepted after the sub-command too, where the
        # parser above leaves it among the arguments of the script.
        late = argparse.ArgumentParser(add_help=False)
        late.add_argument("--build-dir", default=args.build_dir)
        found, rest = late.parse_known_args(rest)
        build_dir = found.build_dir

        names = []
        if args.sub != "budget":
            elves = sorted(Path(build_dir).glob("**/zephyr/zephyr.elf"))
            if not elves:
                self.die(f"no zephyr.elf under {build_dir}: pass --build-dir")
            # A sysbuild tree holds several images: take the one with claims.
            found = next(filter(None, map(channel_names, elves)), {})
            names = [f"--name={ch}={label}" for ch, label in sorted(found.items())]
        sys.exit(subprocess.call([sys.executable, SCRIPTS / OURS[args.sub], *names, *rest]))


def channel_names(elf: Path) -> dict[int, str]:
    """The channels claimed in an image: {channel: name}."""
    from elftools.elf.elffile import ELFFile

    with elf.open("rb") as f:
        section = ELFFile(f).get_section_by_name("ppk2_trace_channel_area")
        data = section.data() if section else b""
    # struct ppk2_trace_channel: one byte of channel, 15 of name.
    return {
        data[at]: data[at + 1 : at + 16].split(b"\0", 1)[0].decode("ascii", "replace")
        for at in range(0, len(data), 16)
    }
