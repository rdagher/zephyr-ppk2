/*
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 *
 * The radio channel: high from the radio's READY event to its DISABLED
 * event, with no code running. The ramp-up before READY is not in it.
 *
 * The nRF Connect SDK has an option for this, CONFIG_MPSL_PIN_DEBUG
 * (nrf/subsys/mpsl/pin_debug). On a kit that is on its board list,
 * enable it: the SDK drives the pin, and this file only names the
 * channel.
 *
 * The list leaves the nRF54LM20 DK out, in v3.3.1 and still on main in
 * November 2026. Without the option, this file routes the two events
 * itself. MPSL publishes the radio's READY and DISABLED events on two
 * DPPI channels; a GPIOTE task on the pin subscribes to them. It
 * follows the pattern of the option for one pin, written from the
 * public interfaces of MPSL and nrfx. That part can go once the option
 * covers the board.
 */
#include <zephyr/init.h>
#include <zephyr/kernel.h>

#include <soc_nrf_common.h>

#include <ppk2_trace.h>

#define RADIO_GPIOS _CONCAT_3(ppk2_d, CONFIG_PPK2_TRACE_RADIO_CHANNEL, _gpios)
#define RADIO_PIN   NRF_DT_GPIOS_TO_PSEL(DT_PATH(zephyr_user), RADIO_GPIOS)

PPK2_TRACE_CLAIM(CONFIG_PPK2_TRACE_RADIO_CHANNEL, radio);

#ifdef CONFIG_MPSL_PIN_DEBUG

BUILD_ASSERT(RADIO_PIN == CONFIG_MPSL_PIN_DEBUG_RADIO_READY_AND_DISABLED_PIN,
	     "the radio channel is not wired to the pin that CONFIG_MPSL_PIN_DEBUG drives");

#else

#include <gpiote_nrfx.h>
#include <helpers/nrfx_gppi.h>
#include <mpsl_dppi_protocol_api.h>
#include <nrfx_gpiote.h>

#define RADIO_GPIOTE NRF_DT_GPIOTE_NODE(DT_PATH(zephyr_user), RADIO_GPIOS)

static int ppk2_trace_radio_init(void)
{
	nrfx_gpiote_t *gpiote = &GPIOTE_NRFX_INST_BY_NODE(RADIO_GPIOTE);
	const nrfx_gpiote_output_config_t output = NRFX_GPIOTE_DEFAULT_OUTPUT_CONFIG;
	const uint32_t radio = nrfx_gppi_domain_id_get((uint32_t)NRF_DPPIC10);
	const uint32_t gpio = nrfx_gppi_domain_id_get((uint32_t)gpiote->p_reg);
	nrfx_gpiote_task_config_t task = {
		.polarity = NRF_GPIOTE_POLARITY_TOGGLE,
		.init_val = NRF_GPIOTE_INITIAL_VALUE_LOW,
	};

	if (nrfx_gpiote_channel_alloc(gpiote, &task.task_ch) != 0 ||
	    nrfx_gpiote_output_configure(gpiote, RADIO_PIN, &output, &task) != 0) {
		return -EIO;
	}

	/* READY sets the pin, DISABLED clears it. */
	const struct {
		uint32_t event;
		uint32_t task;
	} links[] = {
		{MPSL_DPPI_RADIO_PUBLISH_READY_CHANNEL_IDX,
		 nrfx_gpiote_set_task_address_get(gpiote, RADIO_PIN)},
		{MPSL_DPPI_RADIO_PUBLISH_DISABLED_CH_IDX,
		 nrfx_gpiote_clr_task_address_get(gpiote, RADIO_PIN)},
	};

	ARRAY_FOR_EACH_PTR(links, link) {
		nrfx_gppi_resource_t source = {.domain_id = radio, .channel = link->event};
		nrfx_gppi_handle_t handle;

		if (nrfx_gppi_ext_conn_alloc(radio, gpio, &handle, &source) < 0) {
			return -ENOMEM;
		}
		if (nrfx_gppi_ep_attach(link->task, handle) < 0) {
			return -EIO;
		}
		nrfx_gppi_conn_enable(handle);
	}
	nrfx_gpiote_out_task_enable(gpiote, RADIO_PIN);
	return 0;
}

SYS_INIT(ppk2_trace_radio_init, POST_KERNEL, CONFIG_KERNEL_INIT_PRIORITY_DEFAULT);

#endif /* CONFIG_MPSL_PIN_DEBUG */
