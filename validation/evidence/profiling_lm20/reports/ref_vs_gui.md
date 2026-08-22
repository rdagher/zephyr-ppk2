# Cross-validation — zephyr-ppk2 CLI ref vs GUI golden

- **zephyr-ppk2 CLI ref:** `/Users/roudy.dagher/dev/perso/ppk2-lib-blog/zephyr-ppk2/ref.csv` — 3,010,560 rows, 30.11 s
- **GUI golden:** `/Users/roudy.dagher/Downloads/ppk-20260822T174656.csv` — 3,000,001 rows, 30.00 s

## Schema

Headers byte-identical: **True**

## Sample rate

| Capture | Rate (Hz) | Δ vs nominal |
|---|---:|---:|
| zephyr-ppk2 CLI ref | 100,000.0 | +0.0000 kHz |
| GUI golden | 100,000.0 | +0.0000 kHz |

## Current statistics

| Statistic | zephyr-ppk2 CLI ref | GUI golden | Δ |
|---|---:|---:|---:|
| Mean (µA) | 234.351 | 225.610 | **+3.87 %** |
| Std  (µA) | 734.292 | 678.181 | +8.27 % |
| Max  (µA) | 177918.660 | 183161.953 | -2.86 % |
| Min  (µA) | 0.000 | 0.000 | — |

## Distributional comparison (Kolmogorov-Smirnov)

Two-sample KS on 100 k subsampled rows from each capture:

- **KS statistic:** 0.0132
- **p-value:** 0.0000

## Logic pins (rate-based, duration-independent)

| Pin | zephyr-ppk2 CLI ref duty (%) | GUI golden duty (%) | zephyr-ppk2 CLI ref edges/s | GUI golden edges/s |
|---|---:|---:|---:|---:|
| D0 | 29.6683 | 30.7224 |  0.465 |  0.500 |
| D1 |  0.7316 |  2.8953 |  0.365 |  0.400 |
| D2 |  7.3186 |  7.3370 |  0.365 |  0.367 |
| D3 |  7.3173 |  7.1446 |  0.365 |  0.367 |
| D4 |  0.0000 |  0.0000 |  0.000 |  0.000 |
| D5 |  0.0000 |  0.0000 |  0.000 |  0.000 |
| D6 |  0.0000 |  0.0000 |  0.000 |  0.000 |
| D7 |  0.0000 |  0.0000 |  0.000 |  0.000 |

## Acceptance contract

- Headers byte-identical: **pass**
- Mean-current Δ within ±1 %: **FAIL** (+3.87 %)
- KS statistic < 0.05: **pass** (0.0132)
