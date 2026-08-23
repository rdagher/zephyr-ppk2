/* The application phases — a TraceScope at the top of each. */
#include <zephyr/kernel.h>

#include <ppk2_trace.hpp>

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

void wakeup()
{
	ppk2::TraceScope mark{ppk2_ch_wakeup};

	busy_ms(20); /* clocks + peripherals up */
}

void measure()
{
	ppk2::TraceScope mark{ppk2_ch_measure};

	busy_ms(120);        /* sample sensor */
	k_sleep(K_MSEC(30)); /* conversion wait */
	busy_ms(50);         /* crunch */
}

bool transmit(int cycle_no)
{
	ppk2::TraceScope mark{ppk2_ch_transmit};

	if (cycle_no % 8 == 7) { /* nothing to send: early return... */
		return false;    /* ...the marker still drops */
	}
	busy_ms(200); /* radio-shaped burst */
	return true;
}
