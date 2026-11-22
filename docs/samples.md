# Samples

What the three samples measure on the bench, their budget checks, and a
comparison with Nordic's app.

The figures below were measured:

- on an
  [nRF54LM20 DK](https://docs.zephyrproject.org/latest/boards/nordic/nrf54lm20dk/doc/index.html);
- with the
  [PPK2](https://www.nordicsemi.com/Products/Development-hardware/Power-Profiler-Kit-2)
  in Source meter mode at 3.3 V;
- on 2026-11-21, unless a section gives another date.

See [`evidence/`](../evidence/README.md) for how the captures were
taken, and where they are.

Each table gives, per channel:

- the number of complete regions;
- their mean width and mean current;
- their charge: the mean ± the standard deviation over the regions,
  then the median.

## Running a sample

Wire the dev kit first: see [Bench](bench.md). Then, to build
`profiling`, flash it, capture and print the report, run:

```sh
west build -b nrf54lm20dk/nrf54lm20b/cpuapp zephyr-ppk2/samples/profiling
west ppk2 run --source --vdd 3.3 -- west flash
west ppk2 capture --source --vdd 3.3 --out trace.csv --seconds 60
west ppk2 attribute trace.csv
```

## `profiling`

A cycle every 2.8 s:

1. `wakeup`: 20 ms busy.
2. `measure`: 120 ms busy, a 30 ms wait, 50 ms busy.
3. `transmit`: 200 ms busy.
4. A 400 ms sleep, inside the cycle.

The busy stretches are busy waits that stand in for real work. The
30 ms wait is a sleep, as a CPU would take while a sensor converts.
Each function starts with `PPK2_TRACE_SCOPE`.

### Report

| Channel | Regions | Width | Mean current | Charge | Median charge |
|---|---|---|---|---|---|
| D0 cycle | 21 | 823.249 ms | 676.55 µA | 557.0 ± 1.8 µC | 557.418 µC |
| D1 wakeup | 22 | 20.161 ms | 1,402.09 µA | 28.267 ± 0.045 µC | 28.264 µC |
| D2 measure | 21 | 201.429 ms | 1,203.09 µA | 242.3 ± 1.6 µC | 241.425 µC |
| D3 transmit | 21 | 201.594 ms | 1,408.66 µA | 283.98 ± 0.15 µC | 283.996 µC |
| Idle | | | 3.02 µA median | | |

On `cycle` and `measure` the spread of the charge is about ten times
that of `transmit`. Both contain a wake-up from sleep, and some of
those carry a burst. They do not move the median.

### Figure

![One cycle of samples/profiling: the current on a log scale, the four marked regions under it, and a table of their figures](img/profiling.png)

In the figure:

- The 30 ms wait inside `measure` shows as a dip.
- The 400 ms sleep is the flat stretch while D0 stays high.
- The spike to 100 mA where the cycle starts is a
  [wake-up burst](../evidence/README.md#wake-up-bursts).

### Budget on one phase

To check `wakeup` against a budget, with a little room above what it
measures, run:

```sh
west ppk2 budget trace.csv --channel 1 --max-uc 32 --max-ms 22 --idle-max-ua 4
```

```text
PASS mean region charge 28.27 µC (budget 32.00 µC)
PASS mean region width 20.16 ms (budget 22.00 ms)
PASS idle median 3.02 µA (budget 4.00 µA)
```

Make `wakeup` 10 ms longer, `busy_ms(30)` in place of `busy_ms(20)`,
then build, flash and capture again. The same command exits 1:

```text
FAIL mean region charge 42.45 µC (budget 32.00 µC)
FAIL mean region width 30.23 ms (budget 22.00 ms)
PASS idle median 3.02 µA (budget 4.00 µA)
```

The report of that capture, taken on 2026-11-22, shows where the charge
went. `measure` and `transmit` are unchanged, and the cycle costs
571.7 µC where it cost 557.0 µC:

| Channel | Regions | Width | Mean current | Charge | Median charge |
|---|---|---|---|---|---|
| D0 cycle | 21 | 833.165 ms | 686.16 µA | 571.7 ± 2.6 µC | 571.779 µC |
| D1 wakeup | 21 | 30.225 ms | 1,404.31 µA | 42.446 ± 0.057 µC | 42.440 µC |
| D2 measure | 21 | 201.369 ms | 1,204.58 µA | 242.6 ± 1.7 µC | 241.438 µC |
| D3 transmit | 21 | 201.504 ms | 1,408.72 µA | 283.86 ± 0.16 µC | 283.829 µC |

## `wrap_profiling`

The same application with no marker in its source:

- `trace.c` lists the four functions with `PPK2_TRACE_WRAP`;
- `CMakeLists.txt` passes them to `ppk2_trace_wrap()`.

The names in the report are those of the functions.

### Report

| Channel | Regions | Width | Mean current | Charge | Median charge |
|---|---|---|---|---|---|
| D0 run_cycle | 21 | 823.238 ms | 671.73 µA | 553.0 ± 1.8 µC | 553.475 µC |
| D1 wakeup | 22 | 20.159 ms | 1,390.59 µA | 28.032 ± 0.047 µC | 28.024 µC |
| D2 measure | 21 | 201.417 ms | 1,195.13 µA | 240.7 ± 1.8 µC | 239.588 µC |
| D3 transmit | 21 | 201.595 ms | 1,397.85 µA | 281.80 ± 0.15 µC | 281.823 µC |
| Idle | | | 3.02 µA median | | |

The widths agree with those of `profiling` within 0.02 ms. The wrapped
build reads 0.7 to 0.8 % lower in current on every channel.

Two captures of one build differ by less: 0.05 % at most between the
two `ppk2 capture` runs of `profiling` in the
[comparison](#comparison-with-nordics-app) below.

### Repeated captures

On 2026-11-22 the two builds were alternated twice on the bench, 60 s
each, in captures that are not kept:

| Build | `transmit`, two captures |
|---|---|
| Marked | 1,408.42 and 1,408.40 µA |
| Wrapped | 1,398.12 and 1,397.79 µA |

So the 0.7 % follows the build and repeats to 0.02 %.

### Code placement

The two builds have the same configuration and the same compiler
options. What differs is where the code sits.

The CPU spends these regions in the delay loop of `k_busy_wait`. The
linker placed that loop at 0x6ff0 in the marked image and at 0x7020 in
the wrapped one. `arm-zephyr-eabi-nm` shows it as `delay_machine_code`.

### Padding test

To test this, the marked sample was built twice more with a few bytes
of padding that move the loop. The builds were captured in turn, 30 s
each. The padded builds and their captures are not kept:

| Build | Address of the loop | `transmit`, two captures |
|---|---|---|
| Marked | 0x6ff0 | 1,408.19 and 1,408.67 µA |
| Marked, 16 bytes of padding | 0x7000 | 1,397.54 and 1,397.04 µA |
| Marked, 48 bytes of padding | 0x7020 | 1,398.66 and 1,398.47 µA |
| Wrapped | 0x7020 | 1,397.06 µA |

Moving the loop in these builds reproduced the lower current. The
padding moves other code as well, so this shows an effect of where the
code is placed, not that the loop's address alone is responsible. Why
the placement matters was not looked into.

### Comparing two builds

A difference of this size between two builds of this sample came from
the layout of the image, not from what the code does. Keep that
possibility in mind when comparing two builds.

## `ble_advertising`

A BLE advertiser that reads a sensor once a second and puts the value
in its advertising data. It marks two channels:

- D0, the radio channel, driven by hardware from the radio's READY
  event to DISABLED;
- D1, the sensor read, a 5 ms busy wait marked in the source.

### Report

| Channel | Regions | Width | Mean current | Charge | Median charge |
|---|---|---|---|---|---|
| D0 radio | 1,701 | 0.198 ms | 4,881.77 µA | 0.967 ± 0.046 µC | 0.958 µC |
| D1 sensor | 59 | 5.042 ms | 1,396.51 µA | 7.04 ± 0.61 µC | 6.928 µC |
| Idle | | | 1.31 µA median | | |

![samples/ble_advertising around one sensor read: four advertising events on D0, the sensor read on D1, and a table of their figures](img/ble_advertising.png)

There are three radio pulses per advertising event, one per
advertising channel, and an event about every 100 ms. The last event
of the figure starts with a wake-up burst.

The 0.967 µC is the charge inside one pulse. The radio's ramp-up
before READY is not in it, so it is less than a transmission costs.

### Spread of the sensor read

The spread of the sensor read has another cause. In 2 of the 59 reads
an advertising event falls inside the read, and the radio's current is
counted in it. Those two cost 10.2 and 10.3 µC, the others 6.9 to
7.0 µC.

A marked region holds whatever the device under test (DUT) draws while
the pin is high. The median shows the read alone.

### Budget on the sensor read

For example, with these budgets the sample passes:

```sh
west ppk2 budget trace.csv --channel 1 --max-uc 8 --max-ms 6 --idle-max-ua 2
```

```text
PASS mean region charge 7.04 µC (budget 8.00 µC)
PASS mean region width 5.04 ms (budget 6.00 ms)
PASS idle median 1.31 µA (budget 2.00 µA)
```

Make the sensor read three times longer, `k_busy_wait(15000)` in
`read_sensor`, then build, flash and capture again. The same command
exits 1:

```text
FAIL mean region charge 21.45 µC (budget 8.00 µC)
FAIL mean region width 15.13 ms (budget 6.00 ms)
PASS idle median 1.31 µA (budget 2.00 µA)
```

The radio and the idle current are unchanged, so the report points at
the sensor read alone.

## Comparison with Nordic's app

Two samples were captured with Nordic's
[Power Profiler app](https://docs.nordicsemi.com/r/bundle/nrf-connect-for-desktop/page/app/pc-nrfconnect-ppk/using_ppk_app.html)
on 2026-11-22, each between two captures of `ppk2 capture`. The same
script reads all six files. See
[`evidence/`](../evidence/README.md#comparison-with-nordics-app) for
the conditions.

### Mean current

The mean current of a region, and the difference of each
`ppk2 capture` from the app, as a share of the app's figure:

| Channel | `ppk2 capture` | The app | `ppk2 capture` | Differences from the app |
|---|---|---|---|---|
| `profiling` D0 cycle | 675.98 µA | 676.43 µA | 675.62 µA | 0.07 %, 0.12 % |
| `profiling` D1 wakeup | 1,399.21 µA | 1,400.24 µA | 1,399.21 µA | 0.07 %, 0.07 % |
| `profiling` D2 measure | 1,199.09 µA | 1,200.08 µA | 1,199.63 µA | 0.08 %, 0.04 % |
| `profiling` D3 transmit | 1,406.25 µA | 1,406.64 µA | 1,406.38 µA | 0.03 %, 0.02 % |
| `ble_advertising` D0 radio | 4,869.49 µA | 4,878.23 µA | 4,886.83 µA | 0.18 %, 0.18 % |
| `ble_advertising` D1 sensor | 1,374.32 µA | 1,395.96 µA | 1,410.93 µA | 1.6 %, 1.1 % |

### Median charge

The median charge of a region:

| Channel | `ppk2 capture` | The app | `ppk2 capture` |
|---|---|---|---|
| `profiling` D0 cycle | 557.534 µC | 558.178 µC | 556.946 µC |
| `profiling` D1 wakeup | 28.205 µC | 28.223 µC | 28.209 µC |
| `profiling` D2 measure | 241.110 µC | 241.200 µC | 241.176 µC |
| `profiling` D3 transmit | 283.593 µC | 283.654 µC | 283.540 µC |
| `ble_advertising` D0 radio | 0.958 µC | 0.958 µC | 0.959 µC |
| `ble_advertising` D1 sensor | 6.912 µC | 6.917 µC | 6.924 µC |

### Agreement

The widths agree within 0.1 ms on `profiling`, and are 0.198 ms for
the radio in all three captures. The idle median is 1.31 µA in all
three captures of `ble_advertising`.

The two tools agree within 0.2 % on the mean current, except on the
sensor read. There the app lies between the two captures of
`ppk2 capture`, which themselves differ by 2.7 %.

The cause is the one given [above](#ble_advertising): an advertising
event falls inside some of the reads.

| Capture | Reads with an advertising event inside |
|---|---|
| First `ppk2 capture` | 1 of 59 |
| The app | 1 of 28 |
| Last `ppk2 capture` | 4 of 59 |

The medians of the charge agree within 0.3 %.

## See also

- [Commands](commands.md): how to read a report and set a budget.
- [Marking code](marking.md): the markers these samples use.
- [`evidence/`](../evidence/README.md): the captures behind these
  figures.
