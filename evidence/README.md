# Evidence

The captures behind the figures of [samples](../docs/samples.md).

| | |
|---|---|
| Date | 2026-11-21 |
| DUT | nRF54LM20 DK, each sample built from this repository with nRF Connect SDK v3.3.1 |
| PPK2 | Source meter mode at 3.3 V, firmware 1.2.4 |
| Capture | `ppk2 capture` of ppk2-lib at commit `ace11d0`, 10 or 12 s from power-on |
| Markers | D0 to D3 on P1.12 to P1.15 |

| File | Sample |
|---|---|
| `profiling.csv.xz` | `samples/profiling` |
| `wrap_profiling.csv.xz` | `samples/wrap_profiling` |
| `ble_advertising.csv.xz` | `samples/ble_advertising` |
| `ble_advertising_regressed.csv.xz` | The same with `k_busy_wait(15000)` in `read_sensor` |
| `ble_advertising_biased.csv.xz` | The same with a constant load of 0.94 mA, see below |

## Reproducing the figures

```sh
python scripts/attribute.py evidence/profiling.csv.xz \
    --name 0=cycle --name 1=wakeup --name 2=measure --name 3=transmit
python scripts/attribute.py evidence/ble_advertising.csv.xz --name 0=radio --name 1=sensor
python scripts/check_budget.py evidence/ble_advertising_regressed.csv.xz --channel 1 \
    --max-uc 8 --max-ms 6 --idle-max-ua 2
just plots
```

The names are passed by hand here. `west ppk2 attribute` reads them
from the image of a build.

## A constant load against the wake-up bursts

When a DUT wakes from sleep, the PPK2 switches range and can report a
few hundred mA for 20 to 30 µs. Nordic's filter removes two such
samples; a third one gets through in about a third of the wake-ups.

To see what those samples are worth, the sample was captured again with
a constant load that keeps the PPK2 out of its two lowest ranges. The
load is four pins, P1.04 to P1.07, set as inputs with their pull-up and
wired to ground. They draw 0.94 mA together.

```sh
python evidence/event_charge.py evidence/ble_advertising.csv.xz \
    evidence/ble_advertising_biased.csv.xz
```

```text
ble_advertising.csv.xz: baseline 1.3 µA, 71 events, charge 5.34 ± 1.74 µC (median 4.13), with a leaked sample: 25
ble_advertising_biased.csv.xz: baseline 942.5 µA, 74 events, charge 4.01 ± 0.12 µC (median 4.00), with a leaked sample: 0
```

With the load, no sample leaks and every advertising event costs
4.0 µC. Without it, the events with no leaked sample cost the same, and
the 25 others read about 3.5 µC more. The leaked samples are therefore
not a current the DUT drew. The charge of an advertising event is
4.0 µC, the median without the load gives it, and the mean without the
load is a third too high.

## Limits

One dev kit and one PPK2, one capture per sample. That ppk2-lib agrees
with Nordic's Power Profiler app is shown in ppk2-lib, not here.
