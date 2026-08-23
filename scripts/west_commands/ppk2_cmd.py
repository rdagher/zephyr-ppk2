"""West extension: drive the PPK2 harness from the west workflow.

``list``/``capture``/``run``/``power`` pass through to ppk2-lib's CLI.
``attribute`` reads the claimed channel names from the built ELF's
registry (the iterable section PPK2_TRACE_CLAIM fills), so the
``--name`` flags are derived from the firmware instead of retyped.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from shutil import which

from west.commands import WestCommand

_MODULE_ROOT = Path(__file__).resolve().parents[2]
_PASSTHROUGH = ("list", "capture", "run", "power")


class Ppk2(WestCommand):
    def __init__(self):
        super().__init__(
            "ppk2",
            "PPK2 power profiling (list / capture / run / power / attribute)",
            "Capture, power, and attribute with the PPK2 harness.\n"
            "list/capture/run/power pass their arguments to ppk2-lib's CLI;\n"
            "attribute names the channels from the built ELF's registry.",
            accepts_unknown_args=True,
        )

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(
            self.name,
            help=self.help,
            description=self.description,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            usage="west ppk2 {list,capture,run,attribute} [args...]",
        )
        parser.add_argument("sub", choices=(*_PASSTHROUGH, "attribute"))
        parser.add_argument("args", nargs=argparse.REMAINDER)
        return parser

    def do_run(self, args, unknown_args):
        tail = [*unknown_args, *args.args]
        if args.sub in _PASSTHROUGH:
            cli = which("ppk2")
            if cli is None:
                self.die(
                    "ppk2 CLI not found — pip install "
                    '"git+https://github.com/rdagher/ppk2-lib"'
                )
            sys.exit(subprocess.call([cli, args.sub, *tail]))
        self._attribute(tail)

    def _attribute(self, argv):
        ap = argparse.ArgumentParser(prog="west ppk2 attribute")
        ap.add_argument("csv", help="GUI-parity capture CSV")
        ap.add_argument("--build-dir", default="build", help="where to find zephyr.elf")
        ns, extra = ap.parse_known_args(argv)

        elf = self._find_elf(Path(ns.build_dir))
        names = _channel_names(elf)
        if names:
            self.inf(
                f"channel names from {elf}: "
                + ", ".join(f"D{ch}={label}" for ch, label in sorted(names.items()))
            )
        else:
            self.wrn(f"no PPK2 channel registry in {elf} — attributing unnamed")
        name_args = [f"--name={ch}={label}" for ch, label in sorted(names.items())]
        script = _MODULE_ROOT / "scripts" / "attribute.py"
        sys.exit(subprocess.call([sys.executable, str(script), ns.csv, *name_args, *extra]))

    def _find_elf(self, build_dir: Path) -> Path:
        hits = sorted(build_dir.glob("**/zephyr/zephyr.elf"))
        if not hits:
            self.die(f"no zephyr.elf under {build_dir} — pass --build-dir")
        return hits[0]


def _channel_names(elf_path: Path) -> dict[int, str]:
    """Decode {channel: name} from the ppk2_trace_channel_area section."""
    from elftools.elf.elffile import ELFFile

    with open(elf_path, "rb") as f:
        section = ELFFile(f).get_section_by_name("ppk2_trace_channel_area")
        if section is None:
            return {}
        data = section.data()
    names: dict[int, str] = {}
    for off in range(0, len(data) - 15, 16):
        ch = data[off]
        label = data[off + 1 : off + 16].split(b"\0", 1)[0].decode("ascii", "replace")
        if label and ch < 8:
            names[ch] = label
    return names
