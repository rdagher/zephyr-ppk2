/**
 * @file
 * @brief PPK2 trace markers — C++ RAII layer on top of ppk2_trace.h.
 *
 * A TraceScope raises a marker on construction and lowers it on
 * destruction, so the marked region survives early returns and
 * exceptions-disabled error paths alike:
 *
 * @code
 *     {
 *         ppk2::TraceScope mark{ppk2_ch_inference};
 *         run_inference();
 *     }   // marker drops here, whatever run_inference did
 * @endcode
 *
 * trace_scope() is the callable-shaped convenience for one-liners:
 *
 * @code
 *     ppk2::trace_scope(ppk2_ch_sweep, whole_sweep);
 * @endcode
 */
#ifndef ZEPHYR_PPK2_INCLUDE_PPK2_TRACE_HPP_
#define ZEPHYR_PPK2_INCLUDE_PPK2_TRACE_HPP_

#include "ppk2_trace.h"

namespace ppk2 {

/* Raw channel constants for unclaimed use (quick experiments). Claimed
 * ppk2_ch_<name> constants are the normal currency — note that
 * PPK2_TRACE_CLAIM needs a literal channel number, not these.
 */
inline constexpr int D0 = 0;
inline constexpr int D1 = 1;
inline constexpr int D2 = 2;
inline constexpr int D3 = 3;
inline constexpr int D4 = 4;
inline constexpr int D5 = 5;
inline constexpr int D6 = 6;
inline constexpr int D7 = 7;

/** @brief RAII guard: channel high for the enclosing scope. */
class TraceScope {
public:
	explicit TraceScope(int ch) : m_ch(ch) { ppk2_trace_set(m_ch, true); }
	~TraceScope() { ppk2_trace_set(m_ch, false); }

	TraceScope(const TraceScope &) = delete;
	TraceScope &operator=(const TraceScope &) = delete;

private:
	int m_ch;
};

/** @brief Run @p body with channel @p ch held high; lowered on scope exit. */
template <typename Body>
inline void trace_scope(int ch, Body &&body)
{
	TraceScope guard{ch};
	body();
}

/**
 * @brief Decorator: wrap @p f so every call runs with @p Ch held high.
 *
 * @code
 *     auto measure_traced = ppk2::traced<ppk2_ch_measure>(measure);
 *     measure_traced();   // bracketed call
 * @endcode
 */
template <int Ch, typename F>
constexpr auto traced(F f)
{
	return [f](auto &&...args) {
		TraceScope guard{Ch};
		return f(static_cast<decltype(args) &&>(args)...);
	};
}

} /* namespace ppk2 */

#endif /* ZEPHYR_PPK2_INCLUDE_PPK2_TRACE_HPP_ */
