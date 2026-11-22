---
name: ppk2-profile
description: Find which code draws the current in a Zephyr application, with a PPK2 and the zephyr-ppk2 module. Mark code with GPIO channels, capture, read the report per channel, and check a change against a budget. Use when asked to profile, reduce or check the power consumption of firmware in a workspace that has this module and a PPK2 on the bench.
---

# ppk2-profile

The module marks code with GPIO pins that the PPK2 samples next to the
current. A report then gives, per channel, the width, the mean and peak
current and the charge of the marked regions. `README.md` has the
interface; this file is the procedure.

## Before starting

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

2. Read the report. Compare the charge of one complete region, in µC:
   a short region at a high current can cost less than a long one at a
   low current. A region includes the regions marked inside it, so do
   not add the rows up. Then compare the charge of the marked regions
   per second with the idle current.
3. If the largest cost is not inside a marked region, mark more, as in
   the table below. Each new channel needs a wired pin. A channel used
   with `PPK2_TRACE_SCOPE` or `ppk2_trace_set` also needs a
   `PPK2_TRACE_CLAIM`. `PPK2_TRACE_WRAP` and the radio option claim
   theirs themselves: a second claim does not build.
4. Change one thing, then build, flash and capture again to `after.csv`
   with the same options and duration.
5. Compare the two reports channel by channel. Two captures of the same
   firmware differ by about 0.1 % on a region that contains no wake-up
   from sleep. On a short region that contains one they differ by a few
   percent: there, compare the median of the charge, which the report
   prints. Two builds are another matter: a difference under about 1 %
   can come from where the linker placed the code, not from the change
   itself. Keep the same markers in both builds, and do not report a
   gain or a loss of that size as a result.
6. To keep the gain, propose a budget for CI:

   ```sh
   west ppk2 budget after.csv --channel 1 --max-uc 8 --max-ms 6 --idle-max-ua 2
   ```

   These budgets are on the mean over the regions, and on the median
   for the idle current. Leave room above the measured mean: for the
   regions that contain a wake-up, and a few percent for what a
   different placement of the code can add.

## Ways to mark

| To mark | Use |
|---|---|
| A function or a block you can edit | `PPK2_TRACE_SCOPE(ch)` at its top |
| A function you should not edit | `PPK2_TRACE_WRAP` in one file, and `ppk2_trace_wrap()` in CMake |
| The radio, on the nRF54L series | `CONFIG_PPK2_TRACE_RADIO=y` |

## Reporting

- Give the figures as the report prints them, with the capture they
  come from, the mode and the voltage.
- The PPK2 measures current. Speak of current and charge. Give an
  energy only with `--vdd`, and say it assumes a constant voltage.
- `west ppk2 plot <csv> --window START END --out fig.png` draws the
  current with the channels under it, when a picture helps.
- If a capture warns about lost samples, say so and capture again.
