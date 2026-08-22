/* The application phases — each annotated at function top. */
#include <zephyr/kernel.h>

#include <ppk2_trace.h>

#include "app.h"

PPK2_TRACE_CLAIM(1, wakeup);
PPK2_TRACE_CLAIM(2, measure);
PPK2_TRACE_CLAIM(3, transmit);

static void busy_ms(int ms)
{
	for (int i = 0; i < ms; i++) {
		k_busy_wait(1000);
	}
}

void wakeup(void)
{
	PPK2_TRACE_FUNCTION(ppk2_ch_wakeup);

	busy_ms(20); /* clocks + peripherals up */
}

int measure(void)
{
	PPK2_TRACE_FUNCTION(ppk2_ch_measure);

	busy_ms(120);        /* sample sensor */
	k_sleep(K_MSEC(30)); /* conversion wait */
	busy_ms(50);         /* crunch */
	return 42;           /* the reading */
}

int transmit(int reading)
{
	PPK2_TRACE_FUNCTION(ppk2_ch_transmit);

	busy_ms(200); /* radio-shaped burst */
	return reading + 1; /* the ack */
}
