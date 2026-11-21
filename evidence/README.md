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

## Wake-up bursts

When a DUT wakes from sleep, the PPK2 switches range and can report a
few hundred mA for 20 to 30 µs. Nordic's filter removes two such
samples; a third one gets through in about a third of the wake-ups.

A check made on 2026-11-21, whose captures are not kept: the BLE sample
was captured with a constant load of 0.94 mA, which keeps the PPK2 out
of its two lowest ranges. No sample leaked then, and an advertising
event cost 4.01 ± 0.12 µC. Without the load it cost 5.34 ± 1.74 µC on
average, with a median of 4.13 µC. So the leaked samples are not a
current the DUT drew, and the median is the figure to trust.

## Limits

One dev kit and one PPK2, one capture per sample. That ppk2-lib agrees
with Nordic's Power Profiler app is shown in ppk2-lib, not here.
