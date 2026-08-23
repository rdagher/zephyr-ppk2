/*
 * C++ variant of the profiling sample: the same phase cycle, with a
 * TraceScope annotation at the top of each function — main() reads as
 * untraced code, and the guard drops on any exit path (see transmit(),
 * which bails out early every 8th cycle).
 *
 * boot:         3 quick pulses on the cycle channel (sync burst)
 * cycle (D0):   wakeup (D1) -> measure (D2) -> transmit (D3)
 *               -> 400 ms in-cycle sleep (cycle still high)
 * between:      2 s deep idle, repeat forever
 *
 * Claims are shared with C by design (see ppk2_trace.h): a second
 * claim of the same channel in another file is a link error.
 */
#include <zephyr/kernel.h>

#include <ppk2_trace.h>

#include "app.h"

static void sync_burst(void)
{
	for (int i = 0; i < 3; i++) { /* < 5 ms pulses */
		ppk2_trace_set(0, true);
		k_busy_wait(1000);
		ppk2_trace_set(0, false);
		k_busy_wait(1000);
	}
}

int main(void)
{
	sync_burst();
	k_sleep(K_MSEC(500));

	for (int n = 0;; n++) {
		run_cycle(n);
		k_sleep(K_SECONDS(2)); /* deep idle between cycles */
	}
	return 0;
}
