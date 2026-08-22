/*
 * Profiling sample: a typical low-power application cycle, one marker
 * per phase — one capture yields time, current, and energy per phase,
 * plus the cycle cost and the sleep floor.
 *
 * boot:         3 quick pulses on D0 (sync burst)
 * cycle (D0):   wakeup (D1) -> measure (D2) -> transmit (D3)
 *               -> 400 ms in-cycle sleep (cycle still high)
 * between:      2 s deep idle, repeat forever
 *
 * Markers are annotated inside each function (PPK2_TRACE_FUNCTION in
 * cycle.c and phases.c), so the calling code reads as untraced code.
 * samples/wrap_profiling runs the same app with the instrumentation
 * moved out entirely (linker wrapping) — diff the two to compare.
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

	while (1) {
		run_cycle();
		k_sleep(K_SECONDS(2)); /* deep idle between cycles */
	}
	return 0;
}
