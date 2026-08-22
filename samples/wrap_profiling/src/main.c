/*
 * Wrap-profiling sample: the same cycle as samples/profiling,
 * instrumented without touching the app. main.c, cycle.c, and phases.c
 * contain no tracing code — the monitored surface is declared once in
 * trace.c and the linker routes every call through its bracketing
 * wrapper (CMakeLists.txt).
 *
 * boot:         3 quick pulses on D0 (sync burst)
 * cycle (D0):   wakeup (D1) -> measure (D2) -> transmit (D3)
 *               -> 400 ms in-cycle sleep (cycle still high)
 * between:      2 s deep idle, repeat forever
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
