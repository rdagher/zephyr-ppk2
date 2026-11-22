# Evidence

The captures behind the figures of [samples](../docs/samples.md). The
ten files weigh 93 MB, so they are kept on the branch `captures` of
this repository, at commit `3c98dc5`, and a west workspace that takes
the module does not download them. To put them in this folder:

```sh
just captures
```

or, without just:

```sh
git fetch origin captures
git archive 3c98dc599f46165426216f9e0d5b9aabd95a40df '*.csv.xz' | tar -x -C evidence
```

| | |
|---|---|
| Date | 2026-11-21 |
| DUT | nRF54LM20 DK, each sample built from this repository with nRF Connect SDK v3.3.1 |
| PPK2 | Source meter mode at 3.3 V, firmware 1.2.4 |
| Capture | `ppk2 capture` of ppk2-lib at commit `17bcec2`, 60 s from power-on, between 22:50 and 22:57 |
| Markers | D0 to D3 on P1.12 to P1.15 |

| File | Sample |
|---|---|
| `profiling.csv.xz` | `samples/profiling` |
| `wrap_profiling.csv.xz` | `samples/wrap_profiling` |
| `ble_advertising.csv.xz` | `samples/ble_advertising` |
| `ble_advertising_regressed.csv.xz` | The same with `k_busy_wait(15000)` in `read_sensor` |

## Capture procedure

The bench is wired as in [bench](../docs/bench.md): the PPK2 in Source
meter mode supplies the nRF54LM20 DK at 3.3 V, and D0 to D3 go to P1.12
to P1.15. Nordic's Power Profiler app is closed. For each sample:

```sh
just build profiling                                   # nRF Connect SDK v3.3.1
ppk2 run --source --vdd 3.3 -- just flash profiling    # the PPK2 powers the DK meanwhile
ppk2 capture --source --vdd 3.3 --seconds 60 --out profiling.csv
xz -9 profiling.csv
```

`ppk2 capture` switches the power on as it starts, so each capture
begins with the boot of the DUT. The four were taken one after the
other, without touching the bench:

| Capture | Started at |
|---|---|
| `profiling` | 22:50:52 |
| `wrap_profiling` | 22:52:18 |
| `ble_advertising` | 22:53:46 |
| `ble_advertising_regressed` | 22:55:30 |

The last one is `ble_advertising` built with `k_busy_wait(15000)` in
place of `k_busy_wait(5000)` in `read_sensor`; that change is not in
the repository.

The host was a Mac with macOS 26.5.1.

## Comparison with Nordic's app

On 2026-11-22 two of the samples were also captured with the Power
Profiler app, each time between two captures of `ppk2 capture`, on the
same bench without touching it. The files are under `app/`.

| Capture | Tool | Started or exported at | Length |
|---|---|---|---|
| `app/profiling_ppk2_1.csv.xz` | `ppk2 capture` | 11:09:19 | 60 s |
| `app/profiling_app.csv.xz` | The app | 11:12:25 | 30 s |
| `app/profiling_ppk2_2.csv.xz` | `ppk2 capture` | 11:15:46 | 60 s |
| `app/ble_advertising_ppk2_1.csv.xz` | `ppk2 capture` | 11:17:01 | 60 s |
| `app/ble_advertising_app.csv.xz` | The app | 11:20:00 | 30 s |
| `app/ble_advertising_ppk2_2.csv.xz` | `ppk2 capture` | 11:21:07 | 60 s |

`ppk2 capture` was that of ppk2-lib at commit `0e262fc`. The app was
Power Profiler 4.4.1 in nRF Connect for Desktop 5.4.1, in the
configuration it starts with. That is every gain at 1, a spike filter
with 3 samples to smooth and coefficients 0.18 and 0.06, and all eight
digital channels shown. Its captures were exported as CSV with the timestamp,
the current and the digital inputs, and start about 0.7 s before the
power is switched on.

[Samples](../docs/samples.md#comparison-with-nordics-app) has the
figures.

## Reproducing the figures

```sh
python scripts/attribute.py evidence/profiling.csv.xz \
    --name 0=cycle --name 1=wakeup --name 2=measure --name 3=transmit
python scripts/attribute.py evidence/ble_advertising.csv.xz --name 0=radio --name 1=sensor
python scripts/check_budget.py evidence/ble_advertising_regressed.csv.xz --channel 1 \
    --max-uc 8 --max-ms 6 --idle-max-ua 2
just plots
python scripts/attribute.py evidence/app/profiling_app.csv.xz \
    --name 0=cycle --name 1=wakeup --name 2=measure --name 3=transmit
```

The names are passed by hand here. `west ppk2 attribute` reads them
from the image of a build.

## Wake-up bursts

When a DUT wakes from sleep, the PPK2 switches range and reports a few
hundred mA for 2 or 3 samples. Nordic's filter handles two. With a
third, its output stays at tens of mA for 40 µs. That happens at about
a third of the wake-ups, in the app's captures as in those of
`ppk2 capture`.

A check made on 2026-11-21, whose captures are not kept: the BLE sample
was captured with a constant load of 0.94 mA, which keeps the PPK2 out
of its two lowest ranges. No sample leaked then, and an advertising
event cost 4.01 ± 0.12 µC. Without the load it cost 5.34 ± 1.74 µC on
average, with a median of 4.13 µC. The load changed the transient and
left the median where it was, which fits a reading produced by the
range switch, as Nordic's own material describes it. It does not rule
out a real inrush current. Either way the median is the figure to
trust for a repeating event.

## Limits

One dev kit and one PPK2, one capture per sample, so 21 cycles of the
profiling samples and 59 sensor reads. The comparison with the app
covers two of the samples, on one day. That ppk2-lib
agrees with the app on a known signal is shown in ppk2-lib.
