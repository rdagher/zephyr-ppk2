/* Boot-time init of the wired trace channels (CONFIG_PPK2_TRACE_AUTO_INIT). */
#include <zephyr/init.h>
#include <zephyr/sys/__assert.h>

#include <ppk2_trace.h>

static int ppk2_trace_sys_init(void)
{
	int err = ppk2_trace_init();

	__ASSERT_NO_MSG(err == 0);
	return err;
}

SYS_INIT(ppk2_trace_sys_init, POST_KERNEL, CONFIG_PPK2_TRACE_INIT_PRIORITY);
