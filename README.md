# zephyr-ppk2

Zephyr module for per-region power profiling with Nordic's Power
Profiler Kit II (PPK2) — the firmware half of a harness whose host
half is [ppk2-lib](https://github.com/rdagher/ppk2-lib). A bracket
drives one of the PPK2's logic inputs high on entry and low on exit —
the context-manager / RAII idea, with a GPIO as the scope. The PPK2
records the pin alongside every current sample (100 kSPS), so the host
can attribute energy, width, and mean current to each bracketed region
at 10 µs granularity.

```c
PPK2_TRACE_CLAIM(0, cycle);              /* own channel D0, name it "cycle" */

void run_cycle(void)
{
    PPK2_TRACE_FUNCTION(ppk2_ch_cycle);  /* D0 high on entry, low on any exit */

    wakeup();                            /* D1 — bracketed the same way */
    transmit(measure());                 /* D2, D3 */
    k_sleep(K_MSEC(400));
}
```

One capture later — the report labels come from the firmware's
claims, read out of `zephyr.elf`:

![west ppk2 capture, then attribution with names from the ELF](docs/demo.png)

([the same session as a GIF](docs/demo.gif))

- **Per-region reports** — energy (µJ), width (ms), mean current (µA)
  per marked region, plus the idle floor. A marker costs a single
  GPIO write.
- **Named regions** — `PPK2_TRACE_CLAIM(0, cycle)` stores the name in
  a ROM section of the image; `west ppk2 attribute` reads it from
  `zephyr.elf` and labels the report — no name flags to keep in sync.
- **`west ppk2 …`** — list, capture, power, run, attribute, from the
  west workspace.
- **CI gate** — energy/width/idle budgets as exit codes; power and
  timing regressions fail the build.
- **Zero cost when off** — `CONFIG_PPK2_TRACE=n` compiles every marker
  to nothing; instrumented code builds unchanged.

## Pick your path

- **Profile your application** — add the module to your workspace
  ([Setup](#setup)), instrument
  ([docs/instrumentation.md](docs/instrumentation.md)), capture and
  attribute ([Everyday use](#everyday-use)).
- **Try the samples first** — wire a dev kit
  ([docs/bench.md](docs/bench.md)) and run the demo apps
  ([docs/samples.md](docs/samples.md)).

Either way you need a PPK2, a west workspace (developed and
bench-validated on NCS v3.3.1; upstream Zephyr works the same way),
and ppk2-lib's CLI on the host:
`pip install "git+https://github.com/rdagher/ppk2-lib"`.

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

3. `#include <ppk2_trace.h>` (or `.hpp`), claim channels, mark regions.

## Everyday use

```sh
west ppk2 list                                   # PPK2s + per-port status
west ppk2 capture --vdd 3.3 --out trace.csv --seconds 30
west ppk2 run --vdd 3.3 -- west flash            # power the DUT for a command
west ppk2 attribute trace.csv --vdd 3.3          # names come from the ELF
```

`list`/`capture`/`run`/`power` pass through to ppk2-lib's CLI.
`attribute` finds `zephyr.elf` under `--build-dir` (default `build`),
reads the region names the claims embedded in the image, and prints
the labelled per-region report. Flash recipes and per-board bench setups:
[docs/bench.md](docs/bench.md).

## Instrumenting your code

The canonical form is a **tracing module** — one file declares the
monitored surface, the linker routes the calls, the monitored code is
untouched (yours or a vendor stack's):

```c
/* src/trace.c — the app's entire monitored surface */
PPK2_TRACE_WRAP(0, int, radio_send, (int payload_len), (payload_len));
```

```cmake
ppk2_trace_wrap(radio_send)
```

Wrap works on cross-TU calls to C-linkage symbols; for what it can't
reach there are function-top annotations, block scopes, begin/end
pairs for split regions, and C++ RAII/decorator forms — the full
picture with constraints is in
[docs/instrumentation.md](docs/instrumentation.md).

## The samples

Three siblings run the same low-power application cycle, one per
instrumentation style: `profiling` (annotations), `wrap_profiling`
(tracing module — file-for-file the same app, zero code touched),
`profiling_cpp` (RAII). Bench-measured on the nRF54LM20DK: cycle
1855 ± 9 µJ, deep idle median 4.16 µA, cross-validated against a
Nordic GUI golden capture to +0.27 % — reference tables, evidence, and
run instructions in [docs/samples.md](docs/samples.md).

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

The budgets are the bench-measured reference + 25% headroom — this
exact gate passes on the reference capture and fails on a deliberately
tightened budget:

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
