/* SPDX-License-Identifier: Apache-2.0 OR MIT */
#include <zephyr/kernel.h>

#include <ppk2_trace.h>

#include "app.h"

PPK2_TRACE_CLAIM(0, cycle);

void run_cycle(void)
{
	PPK2_TRACE_SCOPE(ppk2_ch_cycle);

	wakeup();
	transmit(measure());
	k_sleep(K_MSEC(400));
}
