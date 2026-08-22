cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(wrap_profiling LANGUAGES C)

target_sources(app PRIVATE src/main.c src/cycle.c src/phases.c src/trace.c)

# The monitored surface — matches the PPK2_TRACE_WRAP list in trace.c.
ppk2_trace_wrap(run_cycle wakeup measure transmit)
