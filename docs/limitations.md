# Limitations

What was not tested, the limits of the markers, and an effect of the
PPK2 that can raise the reading of a short region.

## Testing

- Measured on one
  [nRF54LM20 DK](https://docs.zephyrproject.org/latest/boards/nordic/nrf54lm20dk/doc/index.html)
  with one
  [PPK2](https://www.nordicsemi.com/Products/Development-hardware/Power-Profiler-Kit-2).
- `profiling` and `wrap_profiling` build for the
  [nRF52840 DK](https://docs.zephyrproject.org/latest/boards/nordic/nrf52840dk/doc/index.html)
  as well, but were not captured on it.
- `ble_advertising` builds for the
  [nRF54L15 DK](https://docs.zephyrproject.org/latest/boards/nordic/nrf54l15dk/doc/index.html)
  as well, with its radio pin driven by the SDK, but was not captured
  on it.
- Apart from the radio channel, the module uses only
  [Zephyr](https://docs.zephyrproject.org/latest/)'s own interfaces. It
  has been built for three Nordic boards only, in an
  [nRF Connect SDK](https://github.com/nrfconnect/sdk-nrf) workspace,
  and run on one.

## Markers

- The [radio channel](marking.md#radio-channel) is only supported on
  the nRF54L series, and on the kits that the SDK's
  `CONFIG_MPSL_PIN_DEBUG` lists.
- Eight channels, one region per channel at a time.
- A marker written by code costs that code a GPIO write at each end.
  Its duration was not measured.

## Wake-up bursts

When a device under test (DUT) wakes from sleep, the PPK2 changes
range. At about a third of the wake-ups, four samples in a row (40 µs)
read between about 30 and 180 mA. The captures of Nordic's
[Power Profiler app](https://docs.nordicsemi.com/r/bundle/nrf-connect-for-desktop/page/app/pc-nrfconnect-ppk/using_ppk_app.html)
show the same bursts.

One burst adds 2 to 5 µC. So a short region that contains a wake-up
can read higher than the others, and so can the mean of a whole
capture.

The [report](commands.md#report) gives the median of the charge next to
its mean. When the two differ, trust the median. See
[`evidence/`](../evidence/README.md#wake-up-bursts) for what is known
about the bursts.

## See also

- [`evidence/`](../evidence/README.md#limitations): the limits of the
  captures behind the figures.
- [Marking code](marking.md)
- [Bench](bench.md)
