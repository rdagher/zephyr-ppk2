# Instrumenting your code

## What instrumentation is here

A bracket drives a claimed logic channel high on entry and low on
exit — context-manager / RAII semantics with a GPIO as the scope. The
PPK2 samples every channel alongside the current, so each bracket
becomes a region the host can price: energy, width, mean current.

A bracket costs one GPIO write per edge. With `CONFIG_PPK2_TRACE=n`
every form below compiles to nothing — instrumented code builds
unchanged.

## Claims: owning a channel

Both families start with a claim. Channels are **claimed**: each
component owns its marker, a second claim of the same channel in
another file is a link error (same file: compile error), and claiming
an unwired channel fails at compile time. The claim also registers
`{channel, name}` in the image's ROM — that registry is where
`west ppk2 attribute` reads the report labels.

```c
PPK2_TRACE_CLAIM(2, sensor);   /* defines ppk2_ch_sensor, registers "sensor" */
```

## Two ways to instrument

- **Link-time** — the tracing module: calls are routed through
  bracketing wrappers at symbol resolution. The monitored code is
  untouched; only cross-TU calls to C-linkage symbols are reachable.
- **In-source** — the bracket is written into the code: function-top
  annotation, block scopes, begin/end pairs, C++ RAII. Universal
  reach, at the price of touching the source.

They are complements: link-time for the standing monitored surface,
in-source for what wrap can't reach and for fine-grained work. Both
emit the same GPIO write pair — the sibling samples measure them
within noise of each other.

## Link-time: the tracing module

One file declares the monitored surface, and the linker routes every
call through a bracketing wrapper:

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
  means C-linkage functions; C++ names mangle, so C++ code uses the
  in-source forms instead.
- Same-TU calls bypass the wrapper **silently** (the build stays
  green, the marker never fires) — structure the monitored surface to
  be called across files. `samples/wrap_profiling` splits `cycle.c`
  and `phases.c` for exactly this reason.

## In-source: brackets in the code

### Function annotation

The linker only interposes calls it resolves. Three common cases never
reach it:

- **`static` functions** never become linker symbols — there is
  nothing for `--wrap` to attach to:

  ```c
  /* sensor.c */
  static int adc_read_raw(void)   /* internal helper: no symbol */
  ```

- **Same-TU calls** are resolved before the linker runs, even for
  global functions. `--wrap=process` links green here and the wrapper
  never fires:

  ```c
  /* app.c */
  int process(int raw) { ... }        /* global, but... */

  void poll(void)
  {
      int v = process(adc_read());    /* ...bypasses __wrap_process */
  }
  ```

- **Inlined calls** disappear entirely — header functions,
  `static inline`, or LTO paste the body at the call site.

For all three, put the bracket inside the function instead — one line
at the top, dropped on every exit path, callers untouched:

```c
/* sensor.c */
PPK2_TRACE_CLAIM(2, adc);

static int adc_read_raw(void)
{
    PPK2_TRACE_FUNCTION(ppk2_ch_adc);  /* high on entry */

    int raw = read_hw();
    if (raw < 0) {
        return -EIO;                   /* marker still drops here */
    }
    return raw;                        /* ...and here */
}
```

`samples/profiling` instruments its whole cycle this way — diff it
against `samples/wrap_profiling` for the side-by-side.

### Blocks and split regions

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

### C++

C++ names mangle, so link-time wrapping is out — the two styles map to
a RAII guard and a decorator instead (`ppk2_trace.hpp`).

The guard brackets the enclosing scope and drops on any exit path:

```cpp
PPK2_TRACE_CLAIM(3, inference);

int infer(const Frame &frame)
{
    ppk2::TraceScope mark{ppk2_ch_inference};  // high on entry

    if (!frame.valid()) {
        return -EINVAL;    // marker drops on the early return
    }
    return run_model(frame);   // ...and on the normal one
}
```

The decorator is the C++ analogue of the tracing module: wrap once,
call the wrapped object — the function itself stays untouched:

```cpp
int transmit(int reading);   // untouched

constexpr auto transmit_traced = ppk2::traced<ppk2_ch_tx>(transmit);

void run_cycle(int reading)
{
    transmit_traced(reading);  // bracketed call
    transmit(reading);         // direct call — bypasses the bracket
}
```

Unlike `--wrap`'s silent same-TU bypass, the decorator's bypass is
visible at the call site: the name says which path you took. For
one-off closures there is also `ppk2::trace_scope(ch, callable)`.
