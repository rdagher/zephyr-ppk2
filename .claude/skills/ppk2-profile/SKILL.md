---
name: ppk2-profile
description: Find which code draws the current in a Zephyr application, with a PPK2 and the zephyr-ppk2 module. Mark code with GPIO channels, capture, read the report per channel, and check a change against a budget. Use when asked to profile, reduce or check the power consumption of firmware in a workspace that has this module and a PPK2 on the bench.
---

# ppk2-profile

The module marks code with GPIO pins that the PPK2 samples next to the
current. A report then gives, per channel, the width, the mean and peak
current and the charge of the marked regions. The interface is described in
`docs/marking.md` and `docs/commands.md`; this file is the procedure.

## Preparation

- `west ppk2 list` must show a PPK2 with a data port. If the port is
  busy, Nordic's Power Profiler app is open: ask the user to quit it.
- Ask which board, which mode (Source meter with `--source`, or Ampere
  meter), and which voltage. Do not guess them.
- Check the overlay for the wired channels (`ppk2-dN-gpios`). At most
  eight, and one region per channel at a time.
- Flashing replaces what is on the board. Say so before the first flash.

## Procedure

1. Measure first, with what is already marked:

   ```sh
   west build -b <board> <app>
   west ppk2 run --source --vdd 3.3 -- west flash
   west ppk2 capture --source --vdd 3.3 --out before.csv --seconds 10
   west ppk2 attribute before.csv
   ```

   `attribute` reads the channel names from `build/`; pass
   `--build-dir` when the build is elsewhere.

   Take the capture with `west ppk2 capture`, as above: it power-cycles
   the device under test (DUT). Do not use `--out` on the `run` command
   that flashes. After a flash the chip stays in debug mode until it is
   power-cycled, so such a recording looks plausible and reads high. An
   idle current many times the expected one means the chip was in debug
   mode.

2. Read the report. Compare the charge of one complete region, in µC:
   a short region at a high current can cost less than a long one at a
   low current. A region includes the regions marked inside it, so do
   not add the rows up. It also includes whatever else the DUT draws
   meanwhile: an interrupt, a radio event. Then compare the charge of
   the marked regions per second with the idle current.
3. If the largest cost is not inside a marked region, mark more, as in
   the table below. Each new channel needs a wired pin. A channel used
   with `PPK2_TRACE_SCOPE` or `ppk2_trace_set` also needs a
   `PPK2_TRACE_CLAIM`. `PPK2_TRACE_WRAP` and the radio option claim
   theirs themselves: a second claim does not build.
4. Change one thing, then build, flash and capture again to
   `after.csv`, as in step 1.
5. Compare the two reports channel by channel. See "Comparing two
   firmwares" below for what makes them comparable.
6. To keep the gain, propose a budget for CI:

   ```sh
   west ppk2 budget after.csv --channel 1 --max-uc 8 --max-ms 6 --idle-max-ua 2
   ```

   These budgets are on the mean over the regions, and on the median
   for the idle current. Leave room above the measured mean: for the
   regions that hold a wake-up or a radio event, and a few percent for
   what a different placement of the code can add.

## Comparing two firmwares

- Mark the same code with the same channel in both builds.
- Take one capture of each with `west ppk2 capture` after its flash,
  so that both start from a power cycle. Use the same mode, voltage
  and duration.
- Compare the median of the charge of that channel, which the report
  prints. On a short region, a wake-up from sleep or a radio event
  falls inside some occurrences and moves the mean by a few percent.
- Two captures of the same firmware already differ: by 0.05 % on the
  phases of `samples/profiling`, by 0.4 % on the radio pulses of
  `samples/ble_advertising`.
- Two builds can differ by the placement of the code alone: 0.7 % on
  one sample of this module. Say so when a gain or a loss you report
  is of that size.

## Ways to mark

| To mark | Use |
|---|---|
| A function or a block you can edit | `PPK2_TRACE_SCOPE(ch)` at its top |
| A function you should not edit | `PPK2_TRACE_WRAP` in one file, and `ppk2_trace_wrap()` in CMake |
| A region that starts in one function and ends in another | `ppk2_trace_set(ch, true)`, then `ppk2_trace_set(ch, false)` |
| The radio | `CONFIG_PPK2_TRACE_RADIO=y`, with `CONFIG_MPSL_PIN_DEBUG=y` on a kit that this SDK option lists |

## Reporting

- Give the figures as the report prints them, with the capture they
  come from, the mode and the voltage.
- The PPK2 measures current. Speak of current and charge. Give an
  energy only with `--vdd`, and say it assumes a constant voltage.
- `west ppk2 plot <csv> --window START END --out fig.png` draws the
  current with the channels under it, when a picture helps.
- If a capture warns about lost samples, say so and capture again.
- If `attribute` refuses a capture with "no sample above 200 µA", the
  DUT was not powered: check the mode and the wiring. For a DUT that
  draws less than that, pass `--power-on-ua`.
