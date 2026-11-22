/*
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 *
 * A low-power application cycle: wakeup, measure and transmit, 400 ms
 * of sleep, then two seconds of sleep before the next cycle. The three
 * phases are busy waits that stand in for real work.
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
