/* The application phases — no tracing code. */
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
	busy_ms(20); /* clocks + peripherals up */
}

int measure(void)
{
	busy_ms(120);        /* sample sensor */
	k_sleep(K_MSEC(30)); /* conversion wait */
	busy_ms(50);         /* crunch */
	return 42;           /* the reading */
}

int transmit(int reading)
{
	busy_ms(200); /* radio-shaped burst */
	return reading + 1; /* the ack */
}
