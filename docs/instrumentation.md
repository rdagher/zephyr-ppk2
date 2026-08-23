# Instrumenting your code

A bracket drives a claimed logic channel high on entry and low on
exit — context-manager / RAII semantics with a GPIO as the scope. The
forms below differ only in where the bracket lives: a linker wrapper,
the function body, a block, or an explicit begin/end pair.

## Claims

Channels are **claimed**: each component owns its marker, a second
claim of the same channel in another file is a link error (same file:
compile error), and claiming an unwired channel fails at compile time.
The claim also registers `{channel, name}` in the image's ROM — that
registry is where `west ppk2 attribute` reads the channel names.

```c
PPK2_TRACE_CLAIM(2, sensor);   /* defines ppk2_ch_sensor, registers "sensor" */
```

## Function monitoring: the tracing module

The canonical way to monitor functions is a **tracing module**: one
file declares the monitored surface, and the linker routes every call
through a bracketing wrapper — the monitored code is untouched:

```c
/* src/trace.c — the app's entire monitored surface */
#include <ppk2_trace.h>

PPK2_TRACE_WRAP(0, int, radio_send, (int payload_len), (payload_len));
PPK2_TRACE_WRAP_VOID(1, sensor_poll, (void), ());
```

```cmake
ppk2_trace_wrap(radio_send sensor_poll)  # -Wl,--wrap=<fn> per function
```

The same mechanism reaches code outside the app — HAL or BLE-stack
calls wrap identically (`ppk2_trace_wrap(bt_le_adv_start)` plus one
declaration in your trace module).

Constraints:

- Wrapping intercepts **cross-TU calls to external symbols** — which
  means C-linkage functions; C++ names mangle, so for C++ code the
  RAII guard and decorator below are the canonical forms instead.
- Same-TU calls bypass the wrapper **silently** (the build stays
  green, the marker never fires) — structure the monitored surface to
  be called across files. `samples/wrap_profiling` splits `cycle.c`
  and `phases.c` for exactly this reason.

## Annotation: when wrap can't reach

For `static`, inlined, or same-TU callees, annotate at function top;
the calling code still reads as untraced code:

```c
static void sample(void)
{
    PPK2_TRACE_FUNCTION(ppk2_ch_sensor); /* drops on any return */

    read_sensor();
    crunch();
}
```

## Fine-grained: blocks and split regions

For a specific block in a debug session, or a region that begins in
one function and ends in a callback (tic/toc style, balancing is on
you):

```c
PPK2_TRACE_SCOPE(ppk2_ch_sensor) {  /* block, drops on fall-out */
    read_sensor();
}

ppk2_trace_begin(ppk2_ch_tx);       /* at the radio request... */
ppk2_trace_end(ppk2_ch_tx);         /* ...in the completion callback */
```

`PPK2_TRACE_SCOPE` is a for-scope: leave it by falling out or with
`PPK2_TRACE_SCOPE_BREAK`; `return`/`goto`/plain `break` skip the
marker drop (see the header doc).

## C++

An early-exit-safe RAII guard and a decorator (`ppk2_trace.hpp`):

```cpp
ppk2::TraceScope mark{ppk2_ch_sensor};             // drops on scope exit
constexpr auto sample_traced = ppk2::traced<ppk2_ch_sensor>(sample);
```

## Cost

A marker is a single GPIO write. With `CONFIG_PPK2_TRACE=n` every form
compiles to nothing — instrumented code builds unchanged.
