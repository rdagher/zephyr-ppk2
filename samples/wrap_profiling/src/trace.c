/*
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 *
 * Everything this application marks, in one file. No other file knows
 * about the markers. CMakeLists.txt lists the same functions.
 */
#include <ppk2_trace.h>

PPK2_TRACE_WRAP_VOID(0, run_cycle, (void), ());
PPK2_TRACE_WRAP_VOID(1, wakeup, (void), ());
PPK2_TRACE_WRAP(2, int, measure, (void), ());
PPK2_TRACE_WRAP(3, int, transmit, (int reading), (reading));
