/*
 * C++ variant of the profiling sample: the same phase cycle, with a
 * TraceScope annotation at the top of each function — run_cycle() and
 * main() read as untraced code, and the guard drops on any exit path
 * (see transmit(), which bails out early every 8th cycle).
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

#include <ppk2_trace.hpp>

PPK2_TRACE_CLAIM(0, cycle);
PPK2_TRACE_CLAIM(1, wakeup);
PPK2_TRACE_CLAIM(2, measure);
PPK2_TRACE_CLAIM(3, transmit);

namespace {

void busy_ms(int ms)
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

void run_cycle(int cycle_no)
{
	ppk2::TraceScope mark{ppk2_ch_cycle};

	wakeup();
	measure();
	(void)transmit(cycle_no);
	k_sleep(K_MSEC(400)); /* in-cycle sleep */
}

void sync_burst()
{
	for (int i = 0; i < 3; i++) { /* < 5 ms pulses */
		ppk2_trace_set(ppk2_ch_cycle, true);
		k_busy_wait(1000);
		ppk2_trace_set(ppk2_ch_cycle, false);
		k_busy_wait(1000);
	}
}

} /* namespace */

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
