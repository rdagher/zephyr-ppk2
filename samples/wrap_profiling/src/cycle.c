/* The application cycle — no tracing code. */
#include <zephyr/kernel.h>

#include "app.h"

void run_cycle(void)
{
	wakeup();
	if (transmit(measure()) != 43) {
		return; /* corrupted dataflow would visibly shorten the cycle */
	}
	k_sleep(K_MSEC(400)); /* in-cycle sleep */
}
