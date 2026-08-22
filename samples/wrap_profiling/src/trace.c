/* The tracing module: the app's entire monitored surface, declared in
 * one place. Nothing else in this sample touches the trace API (main's
 * sync burst aside). CMakeLists.txt routes the calls here via
 * ppk2_trace_wrap().
 */
#include <ppk2_trace.h>

PPK2_TRACE_WRAP_VOID(0, run_cycle, (void), ());
PPK2_TRACE_WRAP_VOID(1, wakeup, (void), ());
PPK2_TRACE_WRAP(2, int, measure, (void), ());
PPK2_TRACE_WRAP(3, int, transmit, (int reading), (reading));
