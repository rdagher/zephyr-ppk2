/**
 * @file
 * @brief PPK2 trace markers — up to 8 channels, C API.
 *
 * Channels map to the PPK2's logic inputs D0..D7 through zephyr,user
 * devicetree properties — declare only the ones you wire:
 *
 * @code{.dts}
 *     / {
 *         zephyr,user {
 *             ppk2-d1-gpios = <&gpio0 29 GPIO_ACTIVE_HIGH>;
 *             ppk2-d2-gpios = <&gpio0 30 GPIO_ACTIVE_HIGH>;
 *         };
 *     };
 * @endcode
 *
 * The PPK2 samples all logic pins with every current sample (100 kSPS),
 * so a marker held high brackets a code region for time, current, and
 * energy attribution with 10 µs granularity. A marker costs a single
 * GPIO write. With CONFIG_PPK2_TRACE=n the markers compile to nothing —
 * instrumented code builds unchanged.
 *
 * With CONFIG_PPK2_TRACE_AUTO_INIT (default y) the wired channels are
 * configured at boot; otherwise call ppk2_trace_init() once.
 *
 * Each component claims its channel once at file scope, then brackets
 * regions — a block, or the whole function:
 *
 * @code
 *     PPK2_TRACE_CLAIM(2, sensor);        // defines ppk2_ch_sensor
 *
 *     PPK2_TRACE_SCOPE(ppk2_ch_sensor) {
 *         read_sensor();
 *     }
 *
 *     static void sample(void)
 *     {
 *         PPK2_TRACE_FUNCTION(ppk2_ch_sensor);  // drops on any return
 *         ...
 *     }
 * @endcode
 *
 * Claims also register {channel, name} in the image's ROM (iterable
 * section), so host tooling can read channel names from the ELF.
 */
#ifndef ZEPHYR_PPK2_INCLUDE_PPK2_TRACE_H_
#define ZEPHYR_PPK2_INCLUDE_PPK2_TRACE_H_

#include <errno.h>
#include <stdbool.h>
#include <stdint.h>

#include <zephyr/drivers/gpio.h>
#include <zephyr/sys/iterable_sections.h>
#include <zephyr/sys/util.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifdef CONFIG_PPK2_TRACE

#define PPK2_TRACE_NODE DT_PATH(zephyr_user)

/** @brief 1 iff channel @p ch (literal 0..7) is wired in the overlay. */
#define PPK2_TRACE_HAS_CH(ch) DT_NODE_HAS_PROP(PPK2_TRACE_NODE, ppk2_d##ch##_gpios)

#define PPK2_TRACE_SPEC_(ch) \
	COND_CODE_1(PPK2_TRACE_HAS_CH(ch), \
		    (GPIO_DT_SPEC_GET(PPK2_TRACE_NODE, ppk2_d##ch##_gpios)), \
		    ({0}))

/* C++ gets ODR-clean comdat entities (C++17 inline); C keeps per-TU statics. */
#ifdef __cplusplus
#define PPK2_TRACE_DATA_ inline
#define PPK2_TRACE_FN_ inline
#else
#define PPK2_TRACE_DATA_ static
#define PPK2_TRACE_FN_ static inline
#endif

/* Unwired channels get a {0} spec; init and set skip them. */
PPK2_TRACE_DATA_ const struct gpio_dt_spec ppk2_trace_pins[8] = {
	PPK2_TRACE_SPEC_(0), PPK2_TRACE_SPEC_(1), PPK2_TRACE_SPEC_(2),
	PPK2_TRACE_SPEC_(3), PPK2_TRACE_SPEC_(4), PPK2_TRACE_SPEC_(5),
	PPK2_TRACE_SPEC_(6), PPK2_TRACE_SPEC_(7),
};

/** @brief One claimed channel, registered in ROM for host tooling. */
struct ppk2_trace_channel {
	uint8_t ch;
	char name[15];
};

/**
 * @brief Configure every wired channel as output, driven low.
 *
 * Called at boot when CONFIG_PPK2_TRACE_AUTO_INIT is set.
 *
 * @retval 0 on success
 * @retval -ENODEV if a wired channel's GPIO controller is not ready
 * @retval -errno from gpio_pin_configure_dt() otherwise
 */
PPK2_TRACE_FN_ int ppk2_trace_init(void)
{
	for (int i = 0; i < 8; i++) {
		if (ppk2_trace_pins[i].port == NULL) {
			continue;
		}
		if (!gpio_is_ready_dt(&ppk2_trace_pins[i])) {
			return -ENODEV;
		}
		int err = gpio_pin_configure_dt(&ppk2_trace_pins[i], GPIO_OUTPUT_INACTIVE);
		if (err) {
			return err;
		}
	}
	return 0;
}

/**
 * @brief Drive channel @p ch (0..7, PPK2 D0..D7) high or low.
 *
 * No-op if the channel is out of range or not wired in the overlay.
 */
PPK2_TRACE_FN_ void ppk2_trace_set(int ch, bool on)
{
	if ((unsigned int)ch > 7) {
		return;
	}
	const struct gpio_dt_spec *pin = &ppk2_trace_pins[ch];

	if (pin->port != NULL) {
		(void)gpio_pin_set_dt(pin, on ? 1 : 0);
	}
}

/**
 * @brief Explicit start marker (tic/toc style) — pair with ppk2_trace_end().
 *
 * The unbalanced-capable idiom: a region may begin in one function and
 * end in another (radio request -> done callback, pre-WFI -> wakeup
 * ISR). Balancing is on you — prefer PPK2_TRACE_SCOPE or
 * PPK2_TRACE_FUNCTION for lexical regions.
 */
PPK2_TRACE_FN_ void ppk2_trace_begin(int ch)
{
	ppk2_trace_set(ch, true);
}

/** @brief Explicit end marker — see ppk2_trace_begin(). */
PPK2_TRACE_FN_ void ppk2_trace_end(int ch)
{
	ppk2_trace_set(ch, false);
}

/* C++ namespace-scope const has internal linkage; extern "C" restores the
 * one external guard symbol so C and C++ claims collide on the same name.
 */
#ifdef __cplusplus
#define PPK2_TRACE_CLAIM_GUARD_(ch) extern "C" const int ppk2_trace_claim_d##ch = (ch)
#else
#define PPK2_TRACE_CLAIM_GUARD_(ch) const int ppk2_trace_claim_d##ch = (ch)
#endif

/**
 * @brief Claim channel @p ch (literal 0..7) under @p name, at file scope.
 *
 * Defines the constant `ppk2_ch_<name>` for call sites and registers
 * {channel, name} in ROM. A second claim of @p ch in another file is a
 * link error (same file: compile error); claiming an unwired channel is
 * a compile error. The constant is local to the claiming file — expose
 * an API from that file rather than re-claiming elsewhere.
 */
#define PPK2_TRACE_CLAIM(ch, name) \
	BUILD_ASSERT(PPK2_TRACE_HAS_CH(ch), \
		     "PPK2_TRACE_CLAIM(" #ch ", " #name "): channel not wired in overlay"); \
	BUILD_ASSERT(sizeof(#name) <= 15, \
		     "PPK2_TRACE_CLAIM(" #ch ", " #name "): name longer than 14 chars"); \
	PPK2_TRACE_CLAIM_GUARD_(ch); \
	STRUCT_SECTION_ITERABLE(ppk2_trace_channel, ppk2_trace_channel_d##ch) = { (ch), #name }; \
	enum { ppk2_ch_##name = (ch) }

#define PPK2_TRACE_SCOPE_(var, ch) \
	for (int var = (ppk2_trace_set((ch), true), 1); var; \
	     ppk2_trace_set((ch), false), var = 0)

/**
 * @brief Mark the attached block: raises @p ch before it, drops it after.
 *
 * Leave the block by falling out, or early with PPK2_TRACE_SCOPE_BREAK.
 * `return`, `goto`, and a plain `break` skip the marker drop (`break`
 * also won't exit an enclosing loop). For whole functions prefer
 * PPK2_TRACE_FUNCTION(); for arbitrary exit paths in C++ use the guard
 * in ppk2_trace.hpp.
 */
#define PPK2_TRACE_SCOPE(ch) PPK2_TRACE_SCOPE_(CONCAT(_ppk2_scope_, __COUNTER__), ch)

/** @brief Early exit from a PPK2_TRACE_SCOPE that still drops the marker. */
#define PPK2_TRACE_SCOPE_BREAK continue

PPK2_TRACE_FN_ void ppk2_trace_drop_(int *ch)
{
	ppk2_trace_set(*ch, false);
}

/**
 * @brief Bracket the whole enclosing function: raises @p ch here, drops
 * it on any exit path, early returns included (__cleanup__, the
 * K_SPINLOCK_ONEXIT mechanism).
 */
#define PPK2_TRACE_FUNCTION(ch) \
	__attribute__((cleanup(ppk2_trace_drop_), unused)) int CONCAT(_ppk2_fn_, __COUNTER__) = \
		(ppk2_trace_set((ch), true), (ch))

/**
 * @brief Monitor function @p fn on channel @p ch via linker wrapping.
 *
 * Claims the channel and defines `__wrap_<fn>` bracketing the real
 * call — the monitored function's source is untouched. Pair with
 * `ppk2_trace_wrap(<fn> ...)` in CMake, which adds `-Wl,--wrap=<fn>`.
 * Works on cross-TU calls to external symbols; `static`, inlined, or
 * same-TU callees can't be wrapped — annotate those instead.
 *
 * @code
 *     PPK2_TRACE_WRAP(0, int, radio_send, (int len), (len));
 * @endcode
 */
#define PPK2_TRACE_WRAP(ch, ret, fn, params, args) \
	PPK2_TRACE_CLAIM(ch, fn); \
	ret __real_##fn params; \
	ret __wrap_##fn params \
	{ \
		PPK2_TRACE_FUNCTION(ppk2_ch_##fn); \
		return __real_##fn args; \
	}

/** @brief PPK2_TRACE_WRAP for void functions. */
#define PPK2_TRACE_WRAP_VOID(ch, fn, params, args) \
	PPK2_TRACE_CLAIM(ch, fn); \
	void __real_##fn params; \
	void __wrap_##fn params \
	{ \
		PPK2_TRACE_FUNCTION(ppk2_ch_##fn); \
		__real_##fn args; \
	}

#else /* !CONFIG_PPK2_TRACE — markers compile to nothing */

#define PPK2_TRACE_HAS_CH(ch) 0

static inline int ppk2_trace_init(void)
{
	return 0;
}

static inline void ppk2_trace_set(int ch, bool on)
{
	(void)ch;
	(void)on;
}

static inline void ppk2_trace_begin(int ch)
{
	(void)ch;
}

static inline void ppk2_trace_end(int ch)
{
	(void)ch;
}

#define PPK2_TRACE_CLAIM(ch, name) enum { ppk2_ch_##name = (ch) }

#define PPK2_TRACE_SCOPE_STUB_(var) for (int var = 1; var; var = 0)
#define PPK2_TRACE_SCOPE(ch) PPK2_TRACE_SCOPE_STUB_(CONCAT(_ppk2_scope_, __COUNTER__))
#define PPK2_TRACE_SCOPE_BREAK continue
#define PPK2_TRACE_FUNCTION(ch)

/* Pass-through wrappers keep the link intact if --wrap is applied anyway. */
#define PPK2_TRACE_WRAP(ch, ret, fn, params, args) \
	PPK2_TRACE_CLAIM(ch, fn); \
	ret __real_##fn params; \
	ret __wrap_##fn params { return __real_##fn args; }

#define PPK2_TRACE_WRAP_VOID(ch, fn, params, args) \
	PPK2_TRACE_CLAIM(ch, fn); \
	void __real_##fn params; \
	void __wrap_##fn params { __real_##fn args; }

#endif /* CONFIG_PPK2_TRACE */

#ifdef __cplusplus
}
#endif

#endif /* ZEPHYR_PPK2_INCLUDE_PPK2_TRACE_H_ */
