/* The application cycle — annotated at function top. */
#include <zephyr/kernel.h>

#include <ppk2_trace.h>

#include "app.h"

PPK2_TRACE_CLAIM(0, cycle);

void run_cycle(void)
{
	PPK2_TRACE_FUNCTION(ppk2_ch_cycle);

	wakeup();
	if (transmit(measure()) != 43) {
		return; /* corrupted dataflow would visibly shorten the cycle */
	}
	k_sleep(K_MSEC(400)); /* in-cycle sleep */
}
