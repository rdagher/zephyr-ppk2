# Bench: wiring, build & flash

## Wiring

Overlays are included for:

| Dev kit | Board target | D0 | D1 | D2 | D3 |
|---|---|---|---|---|---|
| nRF52840 DK | `nrf52840dk/nrf52840` | P0.28 (A2) | P0.29 (A3) | P0.30 (A4) | P0.31 (A5) |
| nRF54LM20DK | `nrf54lm20dk/nrf54lm20b/cpuapp` | P1.12 | P1.13 | P1.14 | P1.15 |

From the PPK2's logic port: `D0..D3` clips to the pins above, `GND` to
DK ground, and `VCC` to the DK's VDD rail — the logic-port VCC sets
the digital-input thresholds, so it must follow the DUT's I/O voltage.
Any other board is one overlay away (`zephyr,user` pins).

## Build & flash

```sh
west build -b nrf54lm20dk/nrf54lm20b/cpuapp zephyr-ppk2/samples/profiling
```

(or `just build [sample] [board]` — see `just --list`.)

With the PPK2 in the DUT's supply path, the SWD port is dead until the
rail is up. Two equivalent recipes:

```sh
# A: hold the rail from a second shell for as long as you need
west ppk2 power on --vdd 3.3 --hold         # Ctrl-C releases
west flash                                  # from another shell

# B: one-shot — power the DUT just for the flash
west ppk2 run --vdd 3.3 -- west flash
```

Source mode (PPK2 supplies the DUT): add `--source --vdd 3.0` to the
`run`/`capture` commands.

## Bench setup: nRF54LM20DK (ammeter, 3.3 V — the reference bench)

DK on USB (powers board + J-Link); pull the current-measurement jumper
and put the PPK2 in series across that header — `VIN` supply side,
`VOUT` nRF side. No isolation switches needed: the reference numbers
in [samples.md](samples.md) were taken with everything connected
(LEDs, SWD, VCOMs routed) and still reach the µA-scale sleep floor.

## Bench setup: nRF52840 DK (source, 3.0 V)

PPK2 `VOUT` → the P21 "External supply" header, then: SW8 ON (power),
SW9 = VDD (take power from P21), SW10 ON (enable P21), and SW6 =
**nRF only** while measuring — it isolates the interface-MCU section
(~85 mA of parasitic floor in DEFAULT) and disconnects LEDs/buttons.
Flip SW6 to DEFAULT once to see the board alive, back to nRF only to
measure; in the measurement position the trace itself is the liveness
signal.
