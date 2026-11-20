# Running the samples

Three siblings run the same low-power application cycle —
**wakeup (D1) → measure (D2) → transmit (D3)** inside a cycle marker
(D0), a 400 ms in-cycle sleep, then 2 s deep idle — each instrumented
a different way. Wire a dev kit first: [bench.md](bench.md).

## Quickstart (nRF54LM20DK, ammeter 3.3 V)

```sh
west build -b nrf54lm20dk/nrf54lm20b/cpuapp zephyr-ppk2/samples/profiling
west ppk2 run --vdd 3.3 -- west flash
west ppk2 capture --vdd 3.3 --out trace.csv --seconds 30
west ppk2 attribute trace.csv --vdd 3.3
```

`attribute` reads the channel names from the built ELF — no `--name`
flags to keep in sync with the firmware.

Every sample opens with three 1 ms pulses on D0: a sync burst that
marks boot in the trace. The report lists pulses shorter than 5 ms as
a burst, not as regions.

## `samples/profiling` — annotation

Phases are annotated inside their functions (`PPK2_TRACE_FUNCTION` in
`cycle.c` and `phases.c`) — the call sites and `main()` are identical
to the untraced version. The dataflow carries a tripwire:
`transmit(measure())` must return the right ack or the cycle visibly
shortens.

Reference numbers (nRF54LM20DK, ammeter 3.3 V, bench-measured 2026-08):

| Region | n | energy | width | mean current | peak¹ |
|---|---|---|---|---|---|
| cycle (D0) | 10 | 1855 ± 9 µJ | 820.7 ms | 685 µA | 176 mA |
| wakeup (D1) | 11 | 100 ± 7 µJ | 20.0 ms | 1509 µA | 18.8 mA |
| measure (D2) | 11 | 805 ± 5 µJ | 200.3 ms | 1218 µA | 126 mA |
| transmit (D3) | 11 | 941 ± 0.4 µJ | 200.3 ms | 1423 µA | 2.0 mA |
| deep idle | | | | median 4.16 µA | |

¹ Raw single-sample maxima include wake-up inrush and the PPK2's
auto-range transients: measure's 126 mA spike is the `k_sleep` wake-up
landing inside the bracket, while transmit — no sleep inside — peaks
at a clean 2.0 mA. Budget raw peaks with generous headroom
(`--workload-max-peak-ua`), or keep the per-region sample vector
(`collect_pulses(..., keep_samples=True)`) and write a robust reducer.

Cross-validated against a Nordic GUI golden capture of the same bench.
Over nine marker-aligned cycles: mean Δ +0.27 %, KS 0.0175. Cycle,
measure and transmit energy agree within 0.12 %; the 20 ms wakeup
phase differs by 3.7 %, inside its cycle-to-cycle spread. Committed
under
[`validation/evidence/profiling_lm20/`](../validation/evidence/profiling_lm20/).

## `samples/wrap_profiling` — the tracing module

File-for-file the same app, instrumented without touching it: the
monitored surface is `src/trace.c` (four wrap declarations) plus
`ppk2_trace_wrap(run_cycle wakeup measure transmit)` in CMake. Diff
the two samples to compare the approaches. Bench-measured within
0.35 % of the annotation sibling on every phase, identical idle floor
— wrapping is measurably free
([`siblings.md`](../validation/evidence/profiling_lm20/siblings.md)).

## `samples/profiling_cpp` — C++ RAII

Same cycle with a `TraceScope` at the top of each function; `transmit`
early-returns every 8th cycle and the guard still drops its marker —
visible on the bench as one lean ~620 ms cycle per eight.
