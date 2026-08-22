# Sibling round: annotation vs wrap vs C++ RAII (2026-08-22)

Back-to-back 30 s captures on the same bench (nRF54LM20DK, ammeter
3.3 V) of the three sibling samples — same app, three instrumentation
styles. All firmwares carry the ack tripwire: `transmit(measure())`
must return 43 through the instrumentation or the cycle visibly
shortens by 400 ms.

| Region | `profiling` (annotation) | `wrap_profiling` (linker wrap) | `profiling_cpp` (RAII) |
|---|---|---|---|
| cycle (D0) | 1859.95 ± 9.59 µJ, 819.95 ms | 1861.20 ± 5.89 µJ, 819.91 ms | 1773 ± 285 µJ, 801.6 ms¹ |
| wakeup (D1) | 95.36 ± 2.60 µJ, 19.99 ms | 95.69 ± 3.16 µJ, 19.99 ms | 96.02 ± 3.29 µJ, 19.98 ms |
| measure (D2) | 807.34 ± 5.95 µJ, 200.00 ms | 808.36 ± 5.75 µJ, 199.97 ms | 806.16 ± 4.76 µJ, 199.91 ms |
| transmit (D3) | 944.16 ± 0.44 µJ, 199.91 ms | 945.56 ± 0.42 µJ, 199.88 ms | 945.43 ± 0.54 µJ, n=10² |
| deep idle | median 4.34 µA | median 4.34 µA | median 4.38 µA |

Findings:

- **Wrapping is measurably free**: every wrap region within 0.35 % of
  the annotation sibling — inside run-to-run noise — and the idle
  floors are identical. The wrapper's cost (one extra call frame per
  region) is invisible at µJ scale.
- **Tripwire passed in all three**: 820 ms cycles mean the ack value
  `43` survived the instrumentation path — including two returning
  wrappers in `wrap_profiling`.
- ¹ ² The C++ twin skips transmit every 8th cycle (early return): one
  lean ~620 ms cycle explains the D0 spread (± 285 µJ ≈ one missing
  945 µJ transmit), and transmit counts n=10, not 11. The skipped
  cycle's RAII pulse (~1 µs) is shorter than the 10 µs sample period
  and leaves no D3 trace — sub-sample markers can escape the PPK2.

Captures not committed for this round (the GUI-parity round above
carries the raw data); regenerate with the commands in the sample
README.
