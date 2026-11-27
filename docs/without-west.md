# Using the module without west

The README sets the module up with west. This page gives the same
steps without it: the build with CMake or twister, and the
`west ppk2` commands called directly.

Each `west ppk2` command runs either the `ppk2` command of
[ppk2-lib](https://github.com/rdagher/ppk2-lib) or a script of the
module. Both can be called directly:

| With west | Without west |
|---|---|
| The module listed in `west.yml` | A clone of the module, named in `EXTRA_ZEPHYR_MODULES` |
| `west ppk2 list`, `capture`, `run`, `power` | `ppk2 list`, `capture`, `run`, `power` |
| `west ppk2 attribute` | `python zephyr-ppk2/scripts/attribute.py` |
| `west ppk2 plot` | `python zephyr-ppk2/scripts/plot.py` |
| `west ppk2 budget` | `python zephyr-ppk2/scripts/check_budget.py` |

To install `ppk2` and what `plot.py` imports, run:

```sh
pip install -r zephyr-ppk2/scripts/requirements.txt
```

The examples below run from the folder that holds `zephyr` and
`zephyr-ppk2`, in a shell set up for Zephyr
(`source zephyr/zephyr-env.sh`).

## Build

[`EXTRA_ZEPHYR_MODULES`](https://nrfconnectdocs.nordicsemi.com/ncs/latest/zephyr/develop/modules.html#integrate-modules-in-zephyr-build-system)
adds the module to the ones that the build already finds. For example,
with CMake and Ninja:

```sh
cmake -GNinja -B build -DBOARD=nrf54lm20dk/nrf54lm20b/cpuapp \
    -DEXTRA_ZEPHYR_MODULES="$PWD/zephyr-ppk2" zephyr-ppk2/samples/profiling
ninja -C build
```

With
[twister](https://nrfconnectdocs.nordicsemi.com/ncs/latest/zephyr/develop/twister/index.html),
called as a script:

```sh
zephyr/scripts/twister -T zephyr-ppk2/samples/profiling \
    -p nrf54lm20dk/nrf54lm20b/cpuapp --build-only \
    -x=EXTRA_ZEPHYR_MODULES="$PWD/zephyr-ppk2"
```

## Capture and report

The scripts take the arguments of the `west ppk2` commands, except
`--build-dir`. They do not read `zephyr.elf`, so name the channels with
`--name`. Without it, the report shows `D0` to `D7`.

```sh
ppk2 capture --source --vdd 3.3 --out trace.csv --seconds 60
python zephyr-ppk2/scripts/attribute.py trace.csv \
    --name 0=cycle --name 1=wakeup --name 2=measure --name 3=transmit
python zephyr-ppk2/scripts/check_budget.py trace.csv \
    --channel 1 --max-uc 32 --max-ms 22 --idle-max-ua 4
```

On the capture of `samples/profiling`, they print the
[report](commands.md#report) and the three lines of the
[CI job](commands.md#ci-job).

## See also

- [Commands](commands.md): the report, the figure and the budgets.
- ppk2-lib's
  [command reference](https://rdagher.github.io/ppk2-lib/user/command/):
  `list`, `capture`, `run` and `power` in detail.
