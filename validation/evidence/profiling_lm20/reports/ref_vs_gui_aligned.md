# Cross-validation — CLI 9 cycles vs GUI 9 cycles

- **CLI 9 cycles:** `/Users/roudy.dagher/dev/perso/ppk2-lib-blog/zephyr-ppk2/ref_9c.csv` — 2,538,670 rows, 26.56 s
- **GUI 9 cycles:** `/Users/roudy.dagher/dev/perso/ppk2-lib-blog/zephyr-ppk2/gui_9c.csv` — 2,538,231 rows, 26.82 s

## Schema

Headers byte-identical: **True**

## Sample rate

| Capture | Rate (Hz) | Δ vs nominal |
|---|---:|---:|
| CLI 9 cycles | 95,572.6 | -4.4274 kHz |
| GUI 9 cycles | 94,652.2 | -5.3478 kHz |

## Current statistics

| Statistic | CLI 9 cycles | GUI 9 cycles | Δ |
|---|---:|---:|---:|
| Mean (µA) | 203.746 | 203.187 | **+0.27 %** |
| Std  (µA) | 670.030 | 633.962 | +5.69 % |
| Max  (µA) | 177918.660 | 183161.953 | -2.86 % |
| Min  (µA) | 0.000 | 0.000 | — |

## Distributional comparison (Kolmogorov-Smirnov)

Two-sample KS on 100 k subsampled rows from each capture:

- **KS statistic:** 0.0175
- **p-value:** 0.0000

## Logic pins (rate-based, duration-independent)

| Pin | CLI 9 cycles duty (%) | GUI 9 cycles duty (%) | CLI 9 cycles edges/s | GUI 9 cycles edges/s |
|---|---:|---:|---:|---:|
| D0 | 29.0940 | 29.0819 |  0.301 |  0.298 |
| D1 |  0.7099 |  0.7093 |  0.301 |  0.298 |
| D2 |  7.1011 |  7.0951 |  0.339 |  0.336 |
| D3 |  7.1001 |  7.0919 |  0.339 |  0.336 |
| D4 |  0.0000 |  0.0000 |  0.000 |  0.000 |
| D5 |  0.0000 |  0.0000 |  0.000 |  0.000 |
| D6 |  0.0000 |  0.0000 |  0.000 |  0.000 |
| D7 |  0.0000 |  0.0000 |  0.000 |  0.000 |

## Acceptance contract

- Headers byte-identical: **pass**
- Mean-current Δ within ±1 %: **pass** (+0.27 %)
- KS statistic < 0.05: **pass** (0.0175)
