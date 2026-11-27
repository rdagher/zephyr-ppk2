# Bench

How the dev kits are wired to the
[PPK2](https://docs.nordicsemi.com/bundle/ug_ppk2/page/UG/ppk/PPK_user_guide_Intro.html)
for the samples, and how they are powered and flashed.

## Wiring

| Dev kit | Board target | D0 | D1 | D2 | D3 |
|---|---|---|---|---|---|
| [nRF54LM20 DK](https://docs.zephyrproject.org/latest/boards/nordic/nrf54lm20dk/doc/index.html) | `nrf54lm20dk/nrf54lm20b/cpuapp` | P1.12 | P1.13 | P1.14 | P1.15 |
| [nRF54L15 DK](https://docs.zephyrproject.org/latest/boards/nordic/nrf54l15dk/doc/index.html) | `nrf54l15dk/nrf54l15/cpuapp` | P1.11 | P2.08 | P1.12 | |
| [nRF52840 DK](https://docs.zephyrproject.org/latest/boards/nordic/nrf52840dk/doc/index.html) | `nrf52840dk/nrf52840` | P0.28 | P0.29 | P0.30 | P0.31 |

From the PPK2's logic port:

- `D0` to `D3` to the pins above;
- `GND` to the board's ground;
- `VCC` to the board's supply.

`VCC` sets the levels at which the digital inputs switch, so it must
follow the voltage of the pins of the device under test (DUT).

Another board needs only an overlay with its `zephyr,user` pins.

## Power and flashing

With the PPK2 in the DUT's supply path, the debug port does not answer
until the power is on. To power the DUT for the flash, or to hold the
power on, run:

```sh
west ppk2 run --source --vdd 3.3 -- west flash     # power the DUT for the flash
west ppk2 power on --source --vdd 3.3 --hold       # or hold it on until Ctrl-C
```

Without `--source`, the PPK2 is in Ampere meter mode and measures a
DUT that has its own supply. In that mode, pass the DUT's voltage to
`--vdd`.

Close
[nRF Connect for Desktop](https://www.nordicsemi.com/Software-and-Tools/Development-Tools/nRF-Connect-for-desktop)
first: while one of its apps is open, the PPK2's port can be busy.

## Wiring check

A wire on the wrong pin does not show in a report: the regions are
there, under another name. To check the wires, build with
`CONFIG_PPK2_TRACE_WIRING_CHECK=y`. At boot, the module then holds each
wired channel high in turn: channel n for n + 1 ms, three times over.
`west ppk2 wiring` reads the widths in a capture from power-on and
prints which digital input saw which channel. For `ble_advertising` on
the nRF54L15 DK:

```sh
west build -b nrf54l15dk/nrf54l15/cpuapp zephyr-ppk2/samples/ble_advertising -- -DCONFIG_PPK2_TRACE_WIRING_CHECK=y
```

Flash it, then capture a few seconds and run the check:

```sh
west ppk2 capture --source --vdd 3.3 --out wiring.csv --seconds 3
west ppk2 wiring wiring.csv
```

```text
SKIP D0 radio: driven by the hardware
PASS D1 sensor: on D1
```

A channel seen on another input, on several or on none is a `FAIL`
line, and the command exits 1. A test firmware with three channels,
two of them declared on each other's pin as two swapped wires would
be, printed:

```text
PASS D0 wakeup: on D0
FAIL D1 measure: on D2
FAIL D2 transmit: on D1
```

The radio channel is skipped, since the hardware drives it. Build
without the option again before measuring: the check adds three regions
per channel to the report.

## nRF54LM20 DK

Put the PPK2 across the kit's current-measurement header, as for
Nordic's
[Power Profiler app](https://docs.nordicsemi.com/r/bundle/nrf-connect-for-desktop/page/app/pc-nrfconnect-ppk/using_ppk_app.html).
Everything else on the board stays connected.

See ppk2-lib's
[getting started](https://github.com/rdagher/ppk2-lib/blob/main/docs/user/getting-started.md#wiring)
page for both wirings, Ampere meter and Source meter.

## nRF54L15 DK

This kit is set up for `ble_advertising` only. D0 is P1.11, the pin
that the SDK drives: see
[Marking code](marking.md#kits-covered-by-the-sdk).

Put the PPK2 across the kit's
[current-measurement header](https://docs.nordicsemi.com/r/bundle/ug_nrf54l15_dk/page/ug/nrf54l15_dk/measurements/current_measurements.html),
P6, as on the nRF54LM20 DK.

In Ampere meter mode the kit supplies the nRF54L15: at
[1.8 V by default](https://docs.nordicsemi.com/r/bundle/ug_nrf54l15_dk/page/ug/nrf54l15_dk/hw_desription/power_supply.html),
or at the voltage set with Nordic's
[Board Configurator](https://docs.nordicsemi.com/bundle/nrf-connect-board-configurator/page/index.html).
In Source meter mode the PPK2 supplies it, at the voltage given to
`--vdd`. The sample was captured in Source meter mode at 3.3 V.

With the jumper removed from the header, the debug probe only shows on
USB while the nRF54L15 is powered, about 2 s after the power comes on.
So hold the power on before flashing: see
[Power and flashing](#power-and-flashing).

## nRF52840 DK

Set switch SW6 to "nRF only" to measure. Otherwise the interface chip
and the LEDs stay on the measured supply. `profiling` and `wrap_profiling`
build for this kit but were not captured on it.

## See also

- [Samples](samples.md): running each sample, and what it measures.
- [Commands](commands.md): the `west ppk2` commands.
- [Limitations](limitations.md)
