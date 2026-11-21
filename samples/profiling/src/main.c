/*
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 *
 * A low-power application cycle: wakeup, measure, transmit, a short
 * sleep, then two seconds of deep idle.
 */
#include <zephyr/kernel.h>

#include "app.h"

int main(void)
{
	while (1) {
		run_cycle();
		k_sleep(K_SECONDS(2));
	}
	return 0;
}
