# zephyr-ppk2

A Zephyr module that tells which code a current was drawn by. It marks
code with GPIO pins that a Nordic Power Profiler Kit II (PPK2) samples
next to the current, and reports the width, the current and the charge
of each marked region. The capture itself is taken by
[ppk2-lib](https://github.com/rdagher/ppk2-lib).

This is an experimental release. The interface may still change.

![A BLE advertiser: the radio on D0, a sensor read on D1, and their figures](docs/img/ble_advertising.png)

## Principle

A PPK2 samples eight digital inputs with every current sample, 100,000
times per second. A pin held high while a piece of code runs therefore
marks, in the capture, the current that code drew. The host adds up
the current while each pin is high.

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
| `CONFIG_PPK2_TRACE_RADIO` | A channel the hardware holds high while the radio is on |

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

The radio's own events raise and drop the pin, through DPPI and GPIOTE.
The channel is claimed under the name `radio`. nRF54L series with
MPSL, which is what the nRF Connect SDK uses for Bluetooth LE.

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
west ppk2 capture --source --vdd 3.3 --out trace.csv --seconds 10
west ppk2 attribute trace.csv                           # the report
west ppk2 plot trace.csv --window 5.3 5.8 --out ble.png # the figure
```

`list`, `capture`, `run` and `power` are the commands of ppk2-lib.
`attribute` and `plot` find `zephyr.elf` under `--build-dir` (default
`build`) and read the names of the claimed channels from it.
`attribute` prints:

```text
capture: 999532 samples, 10.00 s powered
D0 radio               n=270   width     0.198 ms  avg   4799.91 µA  peak    10343 µA  charge     0.951 ± 0.031 µC (median 0.954)
D1 sensor              n=9     width     5.040 ms  avg   1371.88 µA  peak     2493 µA  charge     6.914 ± 0.021 µC (median 6.913)
idle (no channel high) median      1.35 µA  mean     26.96 µA
```

A region is a stretch where a channel is high. The charge is given as
the mean ± the standard deviation over the regions, then the median. `--vdd 3.3` adds an
energy column, the charge times that voltage.

`plot` draws the figure at the top of this page from the same capture.
It needs matplotlib and numpy in west's Python environment.

## Budget check

`west ppk2 budget` exits 1 when the regions of a channel, or the idle
current, exceed a budget. In a CI job on a runner wired to the bench:

```sh
west build -b nrf54lm20dk/nrf54lm20b/cpuapp app
west ppk2 run --source --vdd 3.3 -- west flash
west ppk2 capture --source --vdd 3.3 --out trace.csv --seconds 10
west ppk2 budget trace.csv --channel 1 --max-uc 8 --max-ms 6 --idle-max-ua 2
```

```text
PASS region charge 6.91 µC (budget 8.00 µC)
PASS region width 5.04 ms (budget 6.00 ms)
PASS idle median 1.35 µA (budget 2.00 µA)
```

The budgets are `--max-ua`, `--max-peak-ua`, `--max-uc`, `--max-ms`,
`--idle-max-ua`, and `--max-uj` with `--vdd`.

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
[`evidence/`](evidence/README.md) the captures behind those figures.

## Limitations

- One nRF54LM20 DK and one PPK2 on the bench. The samples build for the
  nRF52840 DK as well, but were not captured on it.
- The radio channel exists for the nRF54L series only.
- Eight channels, one region per channel at a time.
- A marker written by code costs that code a GPIO write at each end,
  a few microseconds.
- When a DUT wakes from sleep, the PPK2 switches range and can report
  a few hundred mA for 20 to 30 µs that the DUT did not draw. A region
  that contains a wake-up can therefore read too high, and so can the
  mean of a whole capture. The report gives the median of the charge
  next to its mean: when the two differ, trust the median.
  [`evidence/`](evidence/README.md) has the measurement, and a way
  around it: a constant load of about 1 mA.

## License

Apache-2.0 OR MIT, at your option.

zephyr-ppk2 is not affiliated with or endorsed by Nordic Semiconductor.
PPK2, Power Profiler Kit and nRF are Nordic's product names.
