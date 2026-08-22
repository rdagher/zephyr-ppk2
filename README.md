# zephyr-ppk2

Zephyr module for per-region power profiling with Nordic's Power
Profiler Kit II (PPK2) — the firmware half of a harness whose host
half is [ppk2-lib](https://github.com/rdagher/ppk2-lib). Code regions
are marked on the PPK2's logic channels; the PPK2 samples them with
every current sample (100 kSPS), and the host attributes energy,
width, and current per region at 10 µs granularity:

![west ppk2: capture, then attribution with names from the ELF](docs/demo.gif)

- **Per-region reports** — energy (µJ), width (ms), mean current (µA)
  per marked region, plus the idle floor. A marker costs a single
  GPIO write.
- **Names declared once** — each claimed channel registers
  `{channel, name}` in the image's ROM; the host reads them from the
  ELF.
- **`west ppk2 …`** — list, capture, power-and-run, attribute, from
  the west workspace.
- **CI gate** — energy/width/idle budgets as exit codes; power and
  timing regressions fail the build.
- **Zero cost when off** — `CONFIG_PPK2_TRACE=n` compiles every marker
  to nothing; instrumented code builds unchanged.

## Requirements

- **Zephyr** via a west workspace. Developed and bench-validated on
  NCS v3.3.1 (the [nrfutil-managed
  install](https://docs.nordicsemi.com/bundle/nrfutil/page/guides/sdk_manager.html)
  at `/opt/nordic/ncs`); plain upstream Zephyr works the same way.
- **ppk2-lib's CLI** on the host:
  `pip install "git+https://github.com/rdagher/ppk2-lib"`.
- **A PPK2** and a dev kit — overlays included for:

  | Dev kit | Board target | D0 | D1 | D2 | D3 |
  |---|---|---|---|---|---|
  | nRF52840 DK | `nrf52840dk/nrf52840` | P0.28 (A2) | P0.29 (A3) | P0.30 (A4) | P0.31 (A5) |
  | nRF54LM20DK | `nrf54lm20dk/nrf54lm20b/cpuapp` | P1.12 | P1.13 | P1.14 | P1.15 |

  From the PPK2's logic port: `D0..D3` clips to the pins above, `GND`
  to DK ground, and `VCC` to the DK's VDD rail — the logic-port VCC
  sets the digital-input thresholds, so it must follow the DUT's I/O
  voltage. Any other board is one overlay away (`zephyr,user` pins).
- Optional: [`just`](https://github.com/casey/just) for the local
  recipes in [`justfile`](justfile).

## Setup

In your `west.yml` — the `west-commands` line is what adds
`west ppk2` to your workspace:

```yaml
  projects:
    - name: zephyr-ppk2
      url: https://github.com/rdagher/zephyr-ppk2
      revision: main
      west-commands: scripts/west-commands.yml
```

(Ad hoc, without the manifest: `-DZEPHYR_EXTRA_MODULES=/path/to/zephyr-ppk2`
— build-only, no west commands.) Then in your app:

1. `CONFIG_PPK2_TRACE=y` in `prj.conf` (needs `CONFIG_GPIO=y`) — the
   wired channels are configured at boot
   (`CONFIG_PPK2_TRACE_AUTO_INIT`).
2. Marker pins in your board overlay, only the ones you wire:

   ```dts
   / {
       zephyr,user {
           ppk2-d0-gpios = <&gpio0 28 GPIO_ACTIVE_HIGH>;
           ppk2-d1-gpios = <&gpio0 29 GPIO_ACTIVE_HIGH>;
       };
   };
   ```

3. `#include <ppk2_trace.h>` (or `.hpp`), claim channels, mark regions
   — see [Instrumenting your code](#instrumenting-your-code).

## Everyday use

```sh
west ppk2 list                                   # PPK2s + per-port status
west ppk2 capture --vdd 3.3 --out trace.csv --seconds 30
west ppk2 run --vdd 3.3 -- west flash            # power the DUT for a command
west ppk2 attribute trace.csv --vdd 3.3          # names come from the ELF
```

`list`/`capture`/`run` pass through to ppk2-lib's CLI.
`attribute` finds `zephyr.elf` under `--build-dir` (default `build`),
reads the claimed channel names from the registry, and prints the
per-region report — nothing to keep in sync with the firmware.

### Build & flash

```sh
west build -b nrf54lm20dk/nrf54lm20b/cpuapp zephyr-ppk2/samples/profiling
```

(or `just build [sample] [board]` — see `just --list`.)

With the PPK2 in the DUT's supply path, the SWD port is dead until the
rail is up. Two equivalent recipes:

```sh
# A: hold the rail from a second shell for as long as you need
ppk2 power on --vdd 3.3 --hold              # Ctrl-C releases
west flash                                  # from another shell

# B: one-shot — power the DUT just for the flash
west ppk2 run --vdd 3.3 -- west flash
```

Source mode (PPK2 supplies the DUT): add `--source --vdd 3.0` to the
`run`/`capture` commands.

### Bench setup: nRF54LM20DK (ammeter, 3.3 V — the reference bench)

DK on USB (powers board + J-Link); pull the current-measurement jumper
and put the PPK2 in series across that header — `VIN` supply side,
`VOUT` nRF side. No isolation switches needed: the reference numbers
below were taken with everything connected (LEDs, SWD, VCOMs routed)
and still reach the µA-scale sleep floor.

### Bench setup: nRF52840 DK (source, 3.0 V)

PPK2 `VOUT` → the P21 "External supply" header, then: SW8 ON (power),
SW9 = VDD (take power from P21), SW10 ON (enable P21), and SW6 =
**nRF only** while measuring — it isolates the interface-MCU section
(~85 mA of parasitic floor in DEFAULT) and disconnects LEDs/buttons.
Flip SW6 to DEFAULT once to see the board alive, back to nRF only to
measure; in the measurement position the trace itself is the liveness
signal.

## Instrumenting your code

Channels are **claimed**: each component owns its marker, a second
claim of the same channel in another file is a link error (same file:
compile error), and claiming an unwired channel fails at compile time.
The claim is also what registers the channel's name in the ELF.

The canonical way to monitor functions is a **tracing module**: one
file declares the monitored surface, and the linker routes every call
through a bracketing wrapper — the monitored code is untouched:

```c
/* src/trace.c — the app's entire monitored surface */
#include <ppk2_trace.h>

PPK2_TRACE_WRAP(0, int, radio_send, (int payload_len), (payload_len));
```

```cmake
ppk2_trace_wrap(radio_send)   # -Wl,--wrap=<fn> for each listed function
```

The same mechanism reaches code outside the app — HAL or BLE-stack
calls wrap identically (`ppk2_trace_wrap(bt_le_adv_start)` plus one
declaration in your trace module).

Wrapping intercepts cross-TU calls to external symbols — which means
C-linkage functions; C++ names mangle, so for C++ code the RAII guard
and decorator below are the canonical forms instead. Same-TU calls
bypass the wrapper **silently** (the build stays green, the marker
never fires), so structure the monitored surface to be called across
files. For callees wrap can't reach — `static`, inlined, or same-TU
functions — annotate at function top; the calling code still reads as
untraced code:

```c
PPK2_TRACE_CLAIM(2, sensor);        /* defines ppk2_ch_sensor */

static void sample(void)
{
    PPK2_TRACE_FUNCTION(ppk2_ch_sensor); /* drops on any return */

    read_sensor();
    crunch();
}
```

The bracketed forms are for fine-grained work — a specific block in a
debug session, or a region that begins in one function and ends in a
callback (tic/toc style, balancing is on you):

```c
PPK2_TRACE_SCOPE(ppk2_ch_sensor) {  /* block, drops on fall-out */
    read_sensor();
}

ppk2_trace_begin(ppk2_ch_tx);       /* at the radio request... */
ppk2_trace_end(ppk2_ch_tx);         /* ...in the completion callback */
```

C++ adds an early-exit-safe RAII guard and a decorator (`ppk2_trace.hpp`):

```cpp
ppk2::TraceScope mark{ppk2_ch_sensor};             // drops on scope exit
constexpr auto sample_traced = ppk2::traced<ppk2_ch_sensor>(sample);
```

## The samples

### `samples/profiling` — the annotation demo

A typical low-power application cycle, one claimed channel per phase:
**wakeup (D1) → measure (D2) → transmit (D3)** inside a cycle marker
(D0), a 400 ms in-cycle sleep, then 2 s deep idle. Phases are
annotated inside their functions — `run_cycle()` and `main()` are
identical to the untraced version — and the dataflow carries a
tripwire: `transmit(measure())` must return the right ack or the cycle
visibly shortens.

Reference numbers (nRF54LM20DK, ammeter 3.3 V, bench-measured 2026-08):

| Region | n | energy | width | mean current |
|---|---|---|---|---|
| cycle (D0) | 10 | 1855 ± 9 µJ | 820.7 ms | 685 µA |
| wakeup (D1) | 11 | 100 ± 7 µJ | 20.0 ms | 1509 µA |
| measure (D2) | 11 | 805 ± 5 µJ | 200.3 ms | 1218 µA |
| transmit (D3) | 11 | 941 ± 0.4 µJ | 200.3 ms | 1423 µA |
| deep idle | | | | median 4.16 µA |

Cross-validated against a Nordic GUI golden capture of the same bench —
aligned mean Δ +0.27 %, KS 0.0175, per-phase energy within 0.15 % —
committed under [`validation/evidence/profiling_lm20/`](validation/evidence/profiling_lm20/).

### `samples/wrap_profiling` — the canonical-pattern sibling

File-for-file the same app, instrumented without touching it: the
monitored surface is `src/trace.c` (four `PPK2_TRACE_WRAP` lines) plus
`ppk2_trace_wrap(run_cycle wakeup measure transmit)` in CMake. Diff
the two samples to compare the approaches. Bench-measured within
0.35 % of the annotation sibling on every phase, identical idle floor
— wrapping is measurably free
([`siblings.md`](validation/evidence/profiling_lm20/siblings.md)).

### `samples/profiling_cpp` — the RAII twin

Same cycle with a `TraceScope` at the top of each function; `transmit`
early-returns every 8th cycle and the guard still drops its marker —
visible on the bench as one lean ~620 ms cycle per eight.

## CI: fail the build on a power regression

`scripts/check_budget.py` turns attribution into a gate — exit 1 when a
region blows its energy, width, or idle-current budget, so power *and*
timing regressions both fail the build. On a self-hosted runner wired
to the bench, the loop is the same commands you run at the desk:

```yaml
jobs:
  power-budget:
    runs-on: [self-hosted, ppk2-bench]
    steps:
      - uses: actions/checkout@v4
      - run: west build -b nrf54lm20dk/nrf54lm20b/cpuapp zephyr-ppk2/samples/profiling
      - run: west ppk2 run --vdd 3.3 -- west flash
      - run: west ppk2 capture --vdd 3.3 --out trace.csv --seconds 30
      - run: python zephyr-ppk2/scripts/check_budget.py trace.csv --vdd 3.3 --channel 0 --workload-max-uj 2300 --workload-max-ms 1025 --idle-max-ua 5.2
```

The budgets above are the bench-measured reference + 25% headroom —
this exact gate passes on the reference capture and fails on a
deliberately tightened budget:

![The gate on the bench: PASS on reference budgets, FAIL when tightened](docs/budget.gif)

## Roadmap

Directions being explored, roughly in order:

- Per-thread energy attribution: a `CONFIG_TRACING` user backend that
  holds a channel high while a watched thread runs — no code changes in
  the app (prototype exists on a branch).
- Rust closure API for the markers.
- Instrument neutrality: split the marker/attribution contract from the
  PPK2 specifics so other power instruments plug in as backends, with
  room for custom extensions.
- A worked example on a real workload (TinyML inference energy).

## License

Apache-2.0 OR MIT, at your option.
