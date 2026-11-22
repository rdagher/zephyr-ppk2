# Samples

Three applications, each with its markers. The figures below were
measured on 2026-11-21 on an nRF54LM20 DK, with the PPK2 in Source
meter mode at 3.3 V. [`evidence/`](../evidence/README.md) says where the captures are.

## Running a sample

Wire the dev kit first: see [bench](bench.md).

```sh
west build -b nrf54lm20dk/nrf54lm20b/cpuapp zephyr-ppk2/samples/profiling
west ppk2 run --source --vdd 3.3 -- west flash
west ppk2 capture --source --vdd 3.3 --out trace.csv --seconds 60
west ppk2 attribute trace.csv
```

## `profiling`

A cycle every 2.8 s: `wakeup` (20 ms busy), `measure` (120 ms busy, a
30 ms wait, 50 ms busy), `transmit` (200 ms busy), then a 400 ms sleep
inside the cycle. Each function starts with `PPK2_TRACE_SCOPE`.

| Channel | Regions | Width | Mean current | Charge | Median charge |
|---|---|---|---|---|---|
| D0 cycle | 21 | 823.249 ms | 676.55 µA | 557.0 ± 1.8 µC | 557.418 µC |
| D1 wakeup | 22 | 20.161 ms | 1,402.09 µA | 28.267 ± 0.045 µC | 28.264 µC |
| D2 measure | 21 | 201.429 ms | 1,203.09 µA | 242.3 ± 1.6 µC | 241.425 µC |
| D3 transmit | 21 | 201.594 ms | 1,408.66 µA | 283.98 ± 0.15 µC | 283.996 µC |
| Idle | | | 3.02 µA median | | |

![One cycle of the profiling sample](img/profiling.png)

The 30 ms wait inside `measure` shows as a dip, and the 400 ms sleep as
the flat stretch while D0 stays high. The spike to 100 mA where the
cycle starts is a wake-up burst, not a current the DUT drew.

## `wrap_profiling`

The same application with no marker in its source. `trace.c` lists the
four functions with `PPK2_TRACE_WRAP`, and `CMakeLists.txt` passes them
to `ppk2_trace_wrap()`. The names in the report are those of the
functions.

| Channel | Regions | Width | Mean current | Charge | Median charge |
|---|---|---|---|---|---|
| D0 run_cycle | 21 | 823.238 ms | 671.73 µA | 553.0 ± 1.8 µC | 553.475 µC |
| D1 wakeup | 22 | 20.159 ms | 1,390.59 µA | 28.032 ± 0.047 µC | 28.024 µC |
| D2 measure | 21 | 201.417 ms | 1,195.13 µA | 240.7 ± 1.8 µC | 239.588 µC |
| D3 transmit | 21 | 201.595 ms | 1,397.85 µA | 281.80 ± 0.15 µC | 281.823 µC |
| Idle | | | 3.02 µA median | | |

The widths agree within 0.02 ms. The wrapped build reads 0.7 to 0.8 %
lower in current on every channel, in this round and in an earlier one.
That is more than two captures of one build differ by (0.05 % in
ppk2-lib's validation), and its cause was not looked for: the two builds are different binaries.

The charge is the mean ± the standard deviation over the regions. On
`cycle` and `measure` the spread is ten times that of `transmit`: both
contain a wake-up from sleep, and some of those carry a
[wake-up burst](../evidence/README.md#wake-up-bursts). The median is
not moved by them.

## `ble_advertising`

A BLE advertiser that reads a sensor once a second and puts the value
in its advertising data. D0 is the radio channel, driven by hardware.
D1 is the sensor read, a 5 ms busy wait marked in the source.

| Channel | Regions | Width | Mean current | Charge | Median charge |
|---|---|---|---|---|---|
| D0 radio | 1,701 | 0.198 ms | 4,881.77 µA | 0.967 ± 0.046 µC | 0.958 µC |
| D1 sensor | 59 | 5.042 ms | 1,396.51 µA | 7.04 ± 0.61 µC | 6.928 µC |
| Idle | | | 1.31 µA median | | |

![The BLE sample around one sensor read](img/ble_advertising.png)

There are three radio pulses per advertising event, one per advertising
channel, and an event about every 100 ms. The last event of the figure
starts with a wake-up burst.

### A regression caught

With the budgets below, the sample passes:

```sh
west ppk2 budget trace.csv --channel 1 --max-uc 8 --max-ms 6 --idle-max-ua 2
```

```text
PASS region charge 7.04 µC (budget 8.00 µC)
PASS region width 5.04 ms (budget 6.00 ms)
PASS idle median 1.31 µA (budget 2.00 µA)
```

Make the sensor read three times longer, `k_busy_wait(15000)` in
`read_sensor`, then build, flash and capture again. The same command
exits 1:

```text
FAIL region charge 21.45 µC (budget 8.00 µC)
FAIL region width 15.13 ms (budget 6.00 ms)
PASS idle median 1.31 µA (budget 2.00 µA)
```

The radio and the idle current are unchanged, so the report points at
the sensor read alone.

## Comparison with Nordic's app

Two samples were captured with the Power Profiler app on 2026-11-22,
each between two captures of `ppk2 capture`. The same script reads all
six files. [`evidence/`](../evidence/README.md#comparison-with-nordics-app)
has the conditions.

Mean current of a region:

| Channel | `ppk2 capture` | The app | `ppk2 capture` | The app against each |
|---|---|---|---|---|
| `profiling` D0 cycle | 675.98 µA | 676.43 µA | 675.62 µA | 0.07 %, 0.12 % |
| `profiling` D1 wakeup | 1,399.21 µA | 1,400.24 µA | 1,399.21 µA | 0.07 %, 0.07 % |
| `profiling` D2 measure | 1,199.09 µA | 1,200.08 µA | 1,199.63 µA | 0.08 %, 0.04 % |
| `profiling` D3 transmit | 1,406.25 µA | 1,406.64 µA | 1,406.38 µA | 0.03 %, 0.02 % |
| `ble_advertising` D0 radio | 4,869.49 µA | 4,878.23 µA | 4,886.83 µA | 0.18 %, 0.18 % |
| `ble_advertising` D1 sensor | 1,374.32 µA | 1,395.96 µA | 1,410.93 µA | 1.6 %, 1.1 % |

Median charge of a region:

| Channel | `ppk2 capture` | The app | `ppk2 capture` |
|---|---|---|---|
| `profiling` D0 cycle | 557.534 µC | 558.178 µC | 556.946 µC |
| `profiling` D2 measure | 241.110 µC | 241.200 µC | 241.176 µC |
| `profiling` D3 transmit | 283.593 µC | 283.654 µC | 283.540 µC |
| `ble_advertising` D0 radio | 0.958 µC | 0.958 µC | 0.959 µC |
| `ble_advertising` D1 sensor | 6.912 µC | 6.917 µC | 6.924 µC |

The widths agree within 0.1 ms on `profiling`, and are 0.198 ms for
the radio in all three captures. The idle median is 1.31 µA in all
three captures of `ble_advertising`.

The two tools agree within 0.2 % on the mean current, except on the
sensor read. There the app lies between the two captures of
`ppk2 capture`, which themselves differ by 2.7 %. Some sensor reads
contain a [wake-up burst](../evidence/README.md#wake-up-bursts), in the
app's capture as in the others, and it moves the mean. The medians of
the charge agree within 0.3 %.
