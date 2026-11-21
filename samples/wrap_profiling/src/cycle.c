/* SPDX-License-Identifier: Apache-2.0 OR MIT */
#include <zephyr/kernel.h>

#include "app.h"

void run_cycle(void)
{
	wakeup();
	transmit(measure());
	k_sleep(K_MSEC(400));
}
