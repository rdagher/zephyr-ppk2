/* SPDX-License-Identifier: Apache-2.0 OR MIT */
#include <zephyr/kernel.h>

#include "app.h"

static void busy_ms(int ms)
{
	for (int i = 0; i < ms; i++) {
		k_busy_wait(1000);
	}
}

void wakeup(void)
{
	busy_ms(20);
}

int measure(void)
{
	busy_ms(120);
	/* The CPU sleeps here, as it would while a sensor converts. */
	k_sleep(K_MSEC(30));
	busy_ms(50);
	return 42;
}

int transmit(int reading)
{
	busy_ms(200);
	return reading + 1;
}
