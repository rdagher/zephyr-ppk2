# zephyr-ppk2

A Zephyr module that measures the current and the charge drawn while
marked code runs. It marks code with GPIO pins that a Nordic Power
Profiler Kit II (PPK2) samples next to the current, and reports the
width, the current and the charge of each marked region. The capture itself is taken by
[ppk2-lib](https://github.com/rdagher/ppk2-lib).

This is an experimental release. The interface may still change.

![A BLE advertiser: the radio on D0, a sensor read on D1, and their figures](docs/img/ble_advertising.png)

## Principle

A PPK2 samples eight digital inputs with every current sample, 100,000
times per second. A pin held high while a piece of code runs therefore
marks, in the capture, the time that code ran. The host adds up the
current of the whole DUT while each pin is high: an interrupt or a
radio event that falls inside a marked region is counted in it.

A marker costs one GPIO write at each end. The radio marker costs
nothing: the hardware drives it. With `CONFIG_PPK2_TRACE=n` every
marker compiles to nothing, and the code builds unchanged.

The PPK2 measures current, so the figures are a current and a charge.
An energy follows once the supply voltage is known: the report adds it
when you pass `--vdd`.

## Marking code

Include `<ppk2_trace.h>`. A channel 0 to 7 is the digital input D0 to
D7 of the PPK2.

```c
PPK2_TRACE_CLAIM(1, sensor);          /* file scope: owns D1, names it "sensor" */

static void read_sensor(void)
{
    PPK2_TRACE_SCOPE(ppk2_ch_sensor); /* high until the function ends */
    ...
}
```

| Interface | Use |
|---|---|
| `PPK2_TRACE_CLAIM(ch, name)` | Claims a channel at file scope. Defines `ppk2_ch_<name>` and stores the name in the image, where the report reads it |
| `PPK2_TRACE_SCOPE(ch)` | Holds the channel high to the end of the enclosing block, on every way out |
| `ppk2_trace_set(ch, on)` | For a region that starts in one function and ends in another |
| `PPK2_TRACE_WRAP(ch, ret, fn, params, args)` | Marks a function at link time, without touching its source |
| `CONFIG_PPK2_TRACE_RADIO` | A channel the hardware holds high from the radio's READY event to DISABLED |

A claim fails to build when its channel is not wired in the
devicetree, and two C files that claim the same channel fail to link.

### Link-time wrapping

To mark a function you cannot or do not want to edit, list it in one
file of your application and in CMake:

```c
/* trace.c */
PPK2_TRACE_WRAP(2, int, measure, (int gain), (gain));
PPK2_TRACE_WRAP_VOID(0, run_cycle, (void), ());
```

```cmake
ppk2_trace_wrap(measure run_cycle)
```

The linker then routes every call to `measure` through a wrapper that
raises the channel. This reaches calls between files only: a `static`
or inlined function cannot be wrapped.

### Radio channel

```
CONFIG_PPK2_TRACE_RADIO=y
CONFIG_PPK2_TRACE_RADIO_CHANNEL=0
```

The radio's own events raise and drop the pin, through DPPI and GPIOTE:
READY raises it and DISABLED drops it. The ramp-up before READY is
outside the marked region, so its charge is that of this window and not
of the whole radio event. The channel is claimed under the name
`radio`; do not claim it again.

This is the one part of the module that is specific to a vendor. It is
for Nordic's nRF54L series under the nRF Connect SDK, whose radio layer
(MPSL) publishes those events, and lives in `src/nordic/`. The rest of
the module is plain Zephyr: devicetree, the GPIO driver and a linker
option.

## Requirements

- A PPK2, and a board with one free GPIO per channel.
- A west workspace. The module is developed on nRF Connect SDK v3.3.1.
- [ppk2-lib](https://github.com/rdagher/ppk2-lib) on the host, in the
  environment west runs from, with Python 3.11 or newer:
  `pip install "git+https://github.com/rdagher/ppk2-lib"`.

Only one program can hold a PPK2: quit Nordic's Power Profiler app
before capturing.

## Setup

Add the module to your `west.yml`. The `west-commands` line is what
adds `west ppk2`:

```yaml
  projects:
    - name: zephyr-ppk2
      url: https://github.com/rdagher/zephyr-ppk2
      revision: main
      west-commands: scripts/west-commands.yml
```

Run `west update`. Then, in the application:

1. `CONFIG_GPIO=y` and `CONFIG_PPK2_TRACE=y` in `prj.conf`.
2. The pins in the board overlay, only the ones you wire:

   ```dts
   / {
       zephyr,user {
           ppk2-d0-gpios = <&gpio1 12 GPIO_ACTIVE_HIGH>;
           ppk2-d1-gpios = <&gpio1 13 GPIO_ACTIVE_HIGH>;
       };
   };
   ```

3. Wire the PPK2's logic port: `D0` to `D7` to those pins, `GND` to the
   board's ground, `VCC` to the board's supply. [Bench](docs/bench.md)
   has the wiring of the supported dev kits.

## Usage

```sh
west ppk2 run --source --vdd 3.3 -- west flash          # power the DUT while it is flashed
west ppk2 capture --source --vdd 3.3 --out trace.csv --seconds 60
west ppk2 attribute trace.csv                           # the report
west ppk2 plot trace.csv --window 5.3 5.8 --out ble.png # the figure
```

![From a terminal: the markers in the source, then list, flash, capture, report and figure](docs/img/workflow.gif)

`list`, `capture`, `run` and `power` are the commands of ppk2-lib.
`attribute` and `plot` find `zephyr.elf` under `--build-dir` (default
`build`) and read the names of the claimed channels from it.
`attribute` prints:

```text
capture: 5999755 samples, 60.00 s powered
D0 radio               n=1701  width     0.198 ms  avg   4881.77 µA  peak    10856 µA  charge     0.967 ± 0.046 µC (median 0.958)
D1 sensor              n=59    width     5.042 ms  avg   1396.51 µA  peak     7541 µA  charge     7.044 ± 0.608 µC (median 6.928)
idle (no channel high) median      1.31 µA  mean     25.55 µA
```

A region is a stretch where a channel is high. The charge is given as
the mean ± the standard deviation over the regions, then the median.
`--vdd 3.3` adds an energy column, the charge times that voltage.

The capture must be at 100,000 samples per second, as `ppk2 capture`
writes it and as the app exports it at full rate. An export at a lower
rate is refused, and so is a capture in which the current never rises
above 200 µA, taken as a DUT that was not powered. `--power-on-ua`
sets that threshold for a DUT that draws less.

`plot` draws the figure at the top of this page from the same capture.
It needs matplotlib and numpy in west's Python environment.

## Budget check

`west ppk2 budget` exits 1 when the mean over the regions of a channel,
or the median idle current, exceeds a budget. It checks means: one
region can be above the budget while the mean is below it. In a CI job on a runner wired to the bench:

```sh
west build -b nrf54lm20dk/nrf54lm20b/cpuapp app
west ppk2 run --source --vdd 3.3 -- west flash
west ppk2 capture --source --vdd 3.3 --out trace.csv --seconds 60
west ppk2 budget trace.csv --channel 1 --max-uc 8 --max-ms 6 --idle-max-ua 2
```

```text
PASS mean region charge 7.04 µC (budget 8.00 µC)
PASS mean region width 5.04 ms (budget 6.00 ms)
PASS idle median 1.31 µA (budget 2.00 µA)
```

The budgets are `--max-ua`, `--max-uc` and `--max-ms` on the mean
current, charge and width of a region, `--max-peak-ua` on the highest
sample of any region, `--idle-max-ua` on the median idle current, and
`--max-uj` with `--vdd`.

Leave a few percent of margin in a budget. Two builds of the same
source differed by 0.7 % in a way that followed where the linker had
placed the code: [samples](docs/samples.md#wrap_profiling) has that
case. For the same reason, compare builds that carry the same markers,
and consider shipping the image you measured, markers included.

## Coding assistants

[`.claude/skills/ppk2-profile/SKILL.md`](.claude/skills/ppk2-profile/SKILL.md)
is a procedure an AI coding assistant can follow to find which code
draws the current: measure, mark more where the cost is, change one
thing, measure again, propose a budget. Every step is one of the
commands above.

## Samples

| Sample | Shows |
|---|---|
| [`samples/profiling`](samples/profiling) | A cycle of wakeup, measure and transmit, marked in the source |
| [`samples/wrap_profiling`](samples/wrap_profiling) | The same cycle, marked at link time from one file |
| [`samples/ble_advertising`](samples/ble_advertising) | A BLE advertiser: the radio by hardware, a sensor read in the source |

[Samples](docs/samples.md) has what each one measures on the bench, and
[`evidence/`](evidence/README.md) how the captures behind those figures
were taken and where they are.

## Limitations

- One nRF54LM20 DK and one PPK2 on the bench. `profiling` and
  `wrap_profiling` build for the nRF52840 DK as well, but were not
  captured on it.
- The radio channel exists for the nRF54L series only. The rest was
  built for two Nordic boards and run on one; it uses nothing of
  Nordic's, but has not been built for another vendor's board.
- Eight channels, one region per channel at a time.
- A marker written by code costs that code a GPIO write at each end,
  a few microseconds.
- When a DUT wakes from sleep, the PPK2 switches range, and at about
  a third of the wake-ups it reads tens of mA for 40 µs. Nordic's app
  shows the same bursts. A region that contains a wake-up can
  therefore read higher than the others, and so can the mean of a
  whole capture. The report gives the median of the charge next to its
  mean: when the two differ, trust the median.
  [`evidence/`](evidence/README.md#wake-up-bursts) has what is known
  about them.

## License

Apache-2.0 OR MIT, at your option.

zephyr-ppk2 is not affiliated with or endorsed by Nordic Semiconductor.
PPK2, Power Profiler Kit and nRF are Nordic's product names.
