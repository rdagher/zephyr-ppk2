# Evidence

The captures behind the figures of [Samples](../docs/samples.md), the
conditions they were taken in, and the commands that redo the figures.

## Download

The twelve files weigh 114 MB. They are kept on the branch `captures`
of this repository, at commit `d5f7476`, so a west workspace that takes
the module does not download them. To put them in this folder, run:

```sh
just captures
```

or, without [just](https://just.systems/):

```sh
git fetch origin captures
git archive d5f74762de50988b90c8e89ec59aee44e19d6ebf '*.csv.xz' | tar -x -C evidence
```

## Conditions

The following table shows the conditions of the captures. Where a
capture differs, its row under [Files](#files) or its section says so.

| Condition | Value |
|---|---|
| Date | 2026-11-21 |
| Device under test (DUT) | nRF54LM20 DK, each sample built from this repository with nRF Connect SDK v3.3.1 |
| PPK2 | Source meter mode at 3.3 V, firmware 1.2.4 |
| Capture | `ppk2 capture` of [ppk2-lib](https://github.com/rdagher/ppk2-lib) at commit `d5986ee`, 60 s from power-on, between 22:50 and 22:57 |
| Markers | D0 to D3 on P1.12 to P1.15 |
| Host | macOS 26.5.1 |

## Files

The following table lists the six files at the top of this folder,
and the sample of each:

| File | Sample |
|---|---|
| `profiling.csv.xz` | `samples/profiling` |
| `wrap_profiling.csv.xz` | `samples/wrap_profiling` |
| `ble_advertising.csv.xz` | `samples/ble_advertising` |
| `ble_advertising_regressed.csv.xz` | The same with `k_busy_wait(15000)` in `read_sensor` |
| `profiling_regressed.csv.xz` | `samples/profiling` with `busy_ms(30)` in `wakeup`, captured on 2026-11-22 at 14:31:58 with ppk2-lib at `fd870c1` |
| `ble_advertising_nrf54l15dk.csv.xz` | `samples/ble_advertising` on another kit: see [nRF54L15 DK](#nrf54l15-dk) |

The other six are under `app/`. See
[Comparison with Nordic's app](#comparison-with-nordics-app) for them.

## Capture procedure

The bench is wired as shown in [Bench](../docs/bench.md). For the
captures:

- the PPK2, in Source meter mode, supplies the nRF54LM20 DK at 3.3 V;
- D0 to D3 go to P1.12 to P1.15;
- Nordic's
  [Power Profiler app](https://docs.nordicsemi.com/r/bundle/nrf-connect-for-desktop/page/app/pc-nrfconnect-ppk/using_ppk_app.html)
  is closed.

Each sample was built, flashed, captured and compressed with:

```sh
just build profiling                                   # nRF Connect SDK v3.3.1
ppk2 run --source --vdd 3.3 -- just flash profiling    # the PPK2 powers the DK meanwhile
ppk2 capture --source --vdd 3.3 --seconds 60 --out profiling.csv
xz -9 profiling.csv
```

`ppk2 capture` switches the power on as it starts, so each capture
begins with the boot of the DUT. The first four were taken one after
the other, without touching the bench:

| Capture | Started at |
|---|---|
| `profiling` | 22:50:52 |
| `wrap_profiling` | 22:52:18 |
| `ble_advertising` | 22:53:46 |
| `ble_advertising_regressed` | 22:55:30 |

Two captures come from a sample with one line changed. Neither change
is in the repository:

| Capture | Changed line |
|---|---|
| `ble_advertising_regressed` | `k_busy_wait(15000)` in place of `k_busy_wait(5000)` in `read_sensor` |
| `profiling_regressed` | `busy_ms(30)` in place of `busy_ms(20)` in `wakeup` |

## nRF54L15 DK

One capture of `samples/ble_advertising` on the
[nRF54L15 DK](https://docs.zephyrproject.org/latest/boards/nordic/nrf54l15dk/doc/index.html),
where the SDK drives the radio channel:

| Condition | Value |
|---|---|
| Date | 2026-11-26, started at 18:58:29 |
| DUT | nRF54L15 DK, the sample built from this repository at commit `7156c23` with nRF Connect SDK v3.3.1 |
| Kit settings | VDD at 3.3 V and both VCOM ports disconnected, set with the Board Configurator |
| PPK2 | Source meter mode at 3.3 V, across the kit's current-measurement header |
| Capture | `ppk2 capture` of ppk2-lib at commit `ae31f04`, 60 s from power-on |
| Markers | D0 on P1.11 and D2 on P1.12, driven by the SDK. D1 on P2.08, driven by the module |
| Host | macOS 26.5.1 |

A capture in Ampere meter mode, taken an hour earlier on the same
bench, gave the same counts, and widths within 0.003 ms. It is not in
the repository.

## Comparison with Nordic's app

On 2026-11-22 two of the samples were also captured with the Power
Profiler app, each time between two captures of `ppk2 capture`, on the
same bench without touching it. The files are under `app/`:

| Capture | Tool | Started or exported at | Length |
|---|---|---|---|
| `app/profiling_ppk2_1.csv.xz` | `ppk2 capture` | 11:09:19 | 60 s |
| `app/profiling_app.csv.xz` | The app | 11:12:25 | 30 s |
| `app/profiling_ppk2_2.csv.xz` | `ppk2 capture` | 11:15:46 | 60 s |
| `app/ble_advertising_ppk2_1.csv.xz` | `ppk2 capture` | 11:17:01 | 60 s |
| `app/ble_advertising_app.csv.xz` | The app | 11:20:00 | 30 s |
| `app/ble_advertising_ppk2_2.csv.xz` | `ppk2 capture` | 11:21:07 | 60 s |

### Versions and settings

`ppk2 capture` came from ppk2-lib at commit `6af8bad`. The app was
Power Profiler 4.4.1 in
[nRF Connect for Desktop](https://www.nordicsemi.com/Software-and-Tools/Development-Tools/nRF-Connect-for-desktop)
5.4.1, in the configuration it starts with:

- every gain at 1;
- a spike filter with 3 samples to smooth and coefficients 0.18 and
  0.06;
- all eight digital channels shown.

Its captures were exported as CSV with the timestamp, the current and
the digital inputs. They start about 0.7 s before the power is switched
on.

See [Samples](../docs/samples.md#comparison-with-nordics-app) for the
figures.

## Reproducing the figures

To redo the figures from the captures, run:

```sh
python scripts/attribute.py evidence/profiling.csv.xz \
    --name 0=cycle --name 1=wakeup --name 2=measure --name 3=transmit
python scripts/check_budget.py evidence/profiling_regressed.csv.xz --channel 1 \
    --max-uc 32 --max-ms 22 --idle-max-ua 4
python scripts/attribute.py evidence/ble_advertising.csv.xz --name 0=radio --name 1=sensor
python scripts/check_budget.py evidence/ble_advertising_regressed.csv.xz --channel 1 \
    --max-uc 8 --max-ms 6 --idle-max-ua 2
python scripts/attribute.py evidence/ble_advertising_nrf54l15dk.csv.xz \
    --name 0=radio --name 1=sensor --name 2=packet
python scripts/attribute.py evidence/app/profiling_app.csv.xz \
    --name 0=cycle --name 1=wakeup --name 2=measure --name 3=transmit
just plots
```

The names are passed by hand here. `west ppk2 attribute` reads them
from the image of a build.

`just plots` redraws the two figures of the documentation. It needs
[uv](https://docs.astral.sh/uv/).

## Wake-up bursts

When a DUT wakes from sleep, the PPK2 changes its measuring range. At
about a third of the wake-ups, four samples in a row then read between
about 30 and 180 mA: 40 µs that add 2 to 5 µC.

### Counts

How often it happens, counted at the advertising events of
`ble_advertising`:

| Capture | Events with a burst |
|---|---|
| `ble_advertising.csv.xz` | 173 of the 567 |
| The app's capture of the same sample | 114 of 274 |

The scripts do not print these counts. A burst that falls inside a
marked region shows in the `peak` column of the report: 152,565 µA on
the `cycle` row of `profiling`.

### Check with a constant load

A check made on 2026-11-21, whose captures are not kept. The BLE sample
was captured with a constant load of 0.94 mA, which keeps the PPK2 out
of its two lowest ranges:

- With the load, no burst appeared, and an advertising event cost
  4.01 ± 0.12 µC, the mean ± the standard deviation over the events.
- Without the load it cost 5.34 ± 1.74 µC, with a median of 4.13 µC.

### Nordic's description

Nordic describes the effect in two places:

- The app's documentation says of its
  [spike filter](https://github.com/nordicsemi/pc-nrfconnect-ppk/blob/v4.4.1/doc/docs/overview.md#spike-filter)
  that after a switch of range the first samples may read higher than
  the actual value.
- Nordic's course on low-power Bluetooth LE explains that
  [switching the shunt](https://academy.nordicsemi.com/courses/designing-low-power-bluetooth-le-products/lessons/lesson-3-tools-and-best-practices-for-power-measurement/topic/current-measurement-fundamentals/#Issues-with-automatic-range-switching)
  steps the voltage of the measured rail, and that the decoupling
  capacitors then draw an inrush current.

The check above fits that description and does not prove it. Either
way the median is the figure to trust for an event that repeats.

See ppk2-lib's
[Principle page](https://github.com/rdagher/ppk2-lib/blob/main/docs/measure/principle.md#limit-waking-from-sleep)
for one such wake-up, and what the spike filter does with it.

## Limitations

- One PPK2 and one nRF54LM20 DK, with a single capture on one
  nRF54L15 DK.
- One capture per sample, so 21 cycles of the profiling samples and 59
  sensor reads.
- The comparison with the app covers two of the samples, on one day.

ppk2-lib's
[validation results](https://github.com/rdagher/ppk2-lib/blob/main/docs/validation/results.md)
show that it agrees with the app on a known signal.

## See also

- [Samples](../docs/samples.md): the figures from these captures.
- [Bench](../docs/bench.md): the wiring of the dev kits.
- [Limitations](../docs/limitations.md): the limits of the module.
