# Bench

How the dev kits are wired to the
[PPK2](https://docs.nordicsemi.com/bundle/ug_ppk2/page/UG/ppk/PPK_user_guide_Intro.html)
for the samples, and how they are powered and flashed.

## Wiring

| Dev kit | Board target | D0 | D1 | D2 | D3 |
|---|---|---|---|---|---|
| [nRF54LM20 DK](https://docs.zephyrproject.org/latest/boards/nordic/nrf54lm20dk/doc/index.html) | `nrf54lm20dk/nrf54lm20b/cpuapp` | P1.12 | P1.13 | P1.14 | P1.15 |
| [nRF52840 DK](https://docs.zephyrproject.org/latest/boards/nordic/nrf52840dk/doc/index.html) | `nrf52840dk/nrf52840` | P0.28 | P0.29 | P0.30 | P0.31 |

From the PPK2's logic port: `D0` to `D3` to the pins above, `GND` to
the board's ground, and `VCC` to the board's supply. `VCC` sets the
levels at which the digital inputs switch, so it must follow the
voltage of the pins of the device under test (DUT).

Another board needs only an overlay with its `zephyr,user` pins.

## Power and flashing

With the PPK2 in the DUT's supply path, the debug port does not answer
until the power is on.

```sh
west ppk2 run --source --vdd 3.3 -- west flash     # power the DUT for the flash
west ppk2 power on --source --vdd 3.3 --hold       # or hold it on until Ctrl-C
```

Without `--source` the PPK2 is in Ampere meter mode and measures a DUT
that has its own supply.

## nRF54LM20 DK

Put the PPK2 across the kit's current-measurement header, as for
Nordic's Power Profiler app. Everything else on the board stays
connected. The
[getting started](https://github.com/rdagher/ppk2-lib/blob/main/docs/user/getting-started.md#wiring)
page of ppk2-lib has both wirings, Ampere meter and Source meter.

## nRF52840 DK

Measure with switch SW6 on "nRF only". Otherwise the interface chip and
the LEDs stay on the measured supply. `profiling` and `wrap_profiling`
build for this kit but were not captured on it.
