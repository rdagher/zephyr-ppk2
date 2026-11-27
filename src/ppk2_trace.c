/* SPDX-License-Identifier: Apache-2.0 OR MIT */
#include <zephyr/drivers/gpio.h>
#include <zephyr/init.h>
#include <zephyr/kernel.h>

#include <ppk2_trace.h>

#define PIN(ch) GPIO_DT_SPEC_GET_OR(DT_PATH(zephyr_user), ppk2_d##ch##_gpios, {0})

/* The radio channel belongs to the hardware: see nordic/ppk2_trace_radio.c. */
#ifdef CONFIG_PPK2_TRACE_RADIO
#define IS_RADIO_CHANNEL(ch) ((ch) == CONFIG_PPK2_TRACE_RADIO_CHANNEL)
#else
#define IS_RADIO_CHANNEL(ch) false
#endif

static const struct gpio_dt_spec pins[] = {
	PIN(0), PIN(1), PIN(2), PIN(3), PIN(4), PIN(5), PIN(6), PIN(7),
};

void ppk2_trace_set(int ch, bool on)
{
	if (ch >= 0 && ch < (int)ARRAY_SIZE(pins) && pins[ch].port != NULL && !IS_RADIO_CHANNEL(ch)) {
		(void)gpio_pin_set_dt(&pins[ch], on);
	}
}

/*
 * The wiring check: each wired channel is held high in turn, channel n
 * for n + 1 ms, three times over. `west ppk2 wiring` reads the widths
 * in a capture and tells which digital input saw which channel.
 */
static void ppk2_trace_wiring_check(void)
{
	for (int round = 0; round < 3; round++) {
		for (int ch = 0; ch < (int)ARRAY_SIZE(pins); ch++) {
			if (pins[ch].port == NULL || IS_RADIO_CHANNEL(ch)) {
				continue;
			}
			ppk2_trace_set(ch, true);
			k_busy_wait(USEC_PER_MSEC * (ch + 1));
			ppk2_trace_set(ch, false);
			k_busy_wait(2 * USEC_PER_MSEC);
		}
	}
}

static int ppk2_trace_init(void)
{
	ARRAY_FOR_EACH_PTR(pins, pin) {
		if (pin->port == NULL || IS_RADIO_CHANNEL(pin - pins)) {
			continue;
		}
		if (!gpio_is_ready_dt(pin)) {
			return -ENODEV;
		}
		int err = gpio_pin_configure_dt(pin, GPIO_OUTPUT_INACTIVE);

		if (err) {
			return err;
		}
	}
	if (IS_ENABLED(CONFIG_PPK2_TRACE_WIRING_CHECK)) {
		ppk2_trace_wiring_check();
	}
	return 0;
}

/* APPLICATION level: after every GPIO controller, expanders included. */
SYS_INIT(ppk2_trace_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);
