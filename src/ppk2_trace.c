/* SPDX-License-Identifier: Apache-2.0 OR MIT */
#include <zephyr/drivers/gpio.h>
#include <zephyr/init.h>

#include <ppk2_trace.h>

#define PIN(ch) GPIO_DT_SPEC_GET_OR(DT_PATH(zephyr_user), ppk2_d##ch##_gpios, {0})

static const struct gpio_dt_spec pins[] = {
	PIN(0), PIN(1), PIN(2), PIN(3), PIN(4), PIN(5), PIN(6), PIN(7),
};

void ppk2_trace_set(int ch, bool on)
{
	if (ch >= 0 && ch < (int)ARRAY_SIZE(pins) && pins[ch].port != NULL) {
		(void)gpio_pin_set_dt(&pins[ch], on);
	}
}

static int ppk2_trace_init(void)
{
	ARRAY_FOR_EACH_PTR(pins, pin) {
		if (pin->port == NULL) {
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
	return 0;
}

/* APPLICATION level: after every GPIO controller, expanders included. */
SYS_INIT(ppk2_trace_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);
