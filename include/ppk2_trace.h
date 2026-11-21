/*
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 *
 * PPK2 trace markers: GPIO pins that a PPK2 samples next to the current.
 * Each channel 0..7 is a digital input D0..D7 of the PPK2. Pins come from
 * devicetree, only the ones you wire:
 *
 *     / { zephyr,user { ppk2-d0-gpios = <&gpio1 12 GPIO_ACTIVE_HIGH>; }; };
 *
 * With CONFIG_PPK2_TRACE=n everything here compiles to nothing.
 */
#ifndef ZEPHYR_PPK2_INCLUDE_PPK2_TRACE_H_
#define ZEPHYR_PPK2_INCLUDE_PPK2_TRACE_H_

#include <stdbool.h>
#include <stdint.h>

#include <zephyr/devicetree.h>
#include <zephyr/sys/iterable_sections.h>
#include <zephyr/sys/util.h>
#include <zephyr/toolchain.h>

#ifdef __cplusplus
extern "C" {
#endif

/** A claimed channel and its name, stored in the image for the host. */
struct ppk2_trace_channel {
	uint8_t ch;
	char name[15];
};

#ifdef CONFIG_PPK2_TRACE

/** Drive channel @p ch high or low. Does nothing for a channel that is not wired. */
void ppk2_trace_set(int ch, bool on);

/**
 * Claim channel @p ch (a literal 0..7) under @p name, at file scope.
 *
 * Defines the constant ppk2_ch_<name> and stores the name in the image,
 * where `west ppk2 attribute` reads it. Fails to build when the channel
 * is not wired, and fails to link when two C files claim the same one.
 */
#define PPK2_TRACE_CLAIM(ch, name) PPK2_TRACE_CLAIM_(ch, name)
#define PPK2_TRACE_CLAIM_(ch, name)                                                                \
	BUILD_ASSERT(DT_NODE_HAS_PROP(DT_PATH(zephyr_user), ppk2_d##ch##_gpios),                   \
		     "channel " #ch " is not wired in the devicetree");                            \
	BUILD_ASSERT(sizeof(#name) <= 15, "channel name " #name " is longer than 14 characters");  \
	const int ppk2_trace_claim_d##ch = (ch);                                                   \
	STRUCT_SECTION_ITERABLE(ppk2_trace_channel, ppk2_trace_channel_d##ch) = {(ch), #name};     \
	enum { ppk2_ch_##name = (ch) }

static inline void ppk2_trace_drop_(const int *ch)
{
	ppk2_trace_set(*ch, false);
}

/**
 * Hold @p ch high from here to the end of the enclosing block.
 *
 * Put it first in a function to mark the whole function. The channel
 * drops on every way out: return, break, goto.
 */
#define PPK2_TRACE_SCOPE(ch)                                                                       \
	__attribute__((cleanup(ppk2_trace_drop_), unused)) const int CONCAT(ppk2_scope_,           \
									    __COUNTER__) =         \
		(ppk2_trace_set((ch), true), (ch))

/**
 * Mark function @p fn on channel @p ch without touching its source.
 *
 * Claims the channel under the function's name and defines the wrapper
 * the linker calls in its place. List @p fn in `ppk2_trace_wrap()` in
 * CMake as well. Reaches calls between files only: a static or inlined
 * function cannot be wrapped.
 *
 *     PPK2_TRACE_WRAP(2, int, measure, (int gain), (gain));
 */
#define PPK2_TRACE_WRAP(ch, ret, fn, params, args)                                                 \
	PPK2_TRACE_CLAIM(ch, fn);                                                                  \
	ret __real_##fn params;                                                                    \
	ret __wrap_##fn params                                                                     \
	{                                                                                          \
		PPK2_TRACE_SCOPE(ppk2_ch_##fn);                                                    \
		return __real_##fn args;                                                           \
	}

/** PPK2_TRACE_WRAP for a function that returns nothing. */
#define PPK2_TRACE_WRAP_VOID(ch, fn, params, args)                                                 \
	PPK2_TRACE_CLAIM(ch, fn);                                                                  \
	void __real_##fn params;                                                                   \
	void __wrap_##fn params                                                                    \
	{                                                                                          \
		PPK2_TRACE_SCOPE(ppk2_ch_##fn);                                                    \
		__real_##fn args;                                                                  \
	}

#else /* !CONFIG_PPK2_TRACE */

static inline void ppk2_trace_set(int ch, bool on)
{
	ARG_UNUSED(ch);
	ARG_UNUSED(on);
}

#define PPK2_TRACE_CLAIM(ch, name) enum { ppk2_ch_##name = (ch) }
#define PPK2_TRACE_SCOPE(ch)

#define PPK2_TRACE_WRAP(ch, ret, fn, params, args) PPK2_TRACE_CLAIM(ch, fn)
#define PPK2_TRACE_WRAP_VOID(ch, fn, params, args) PPK2_TRACE_CLAIM(ch, fn)

#endif /* CONFIG_PPK2_TRACE */

#ifdef __cplusplus
}
#endif

#endif /* ZEPHYR_PPK2_INCLUDE_PPK2_TRACE_H_ */
