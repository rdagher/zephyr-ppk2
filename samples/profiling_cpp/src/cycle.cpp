/* The application cycle — a TraceScope at the top. */
#include <zephyr/kernel.h>

#include <ppk2_trace.hpp>

#include "app.h"

PPK2_TRACE_CLAIM(0, cycle);

void run_cycle(int cycle_no)
{
	ppk2::TraceScope mark{ppk2_ch_cycle};

	wakeup();
	measure();
	(void)transmit(cycle_no);
	k_sleep(K_MSEC(400)); /* in-cycle sleep */
}
