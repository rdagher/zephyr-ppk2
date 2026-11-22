/*
 * SPDX-License-Identifier: Apache-2.0 OR MIT
 *
 * A BLE advertiser that reads a sensor once a second and puts the value
 * in its advertising data. D0 is the radio, raised by hardware
 * (CONFIG_PPK2_TRACE_RADIO). D1 is the sensor read, a 5 ms busy wait
 * that stands in for one.
 */
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/kernel.h>

#include <ppk2_trace.h>

PPK2_TRACE_CLAIM(1, sensor);

static uint8_t reading[] = {0xff, 0xff, 0x00}; /* manufacturer data: test company ID, value */

static const struct bt_data ad[] = {
	BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_NO_BREDR),
	BT_DATA(BT_DATA_MANUFACTURER_DATA, reading, sizeof(reading)),
};

static void read_sensor(void)
{
	PPK2_TRACE_SCOPE(ppk2_ch_sensor);

	k_busy_wait(5000);
	reading[2]++;
}

int main(void)
{
	if (bt_enable(NULL) != 0 ||
	    bt_le_adv_start(BT_LE_ADV_NCONN, ad, ARRAY_SIZE(ad), NULL, 0) != 0) {
		return 0;
	}
	while (1) {
		k_sleep(K_SECONDS(1));
		read_sensor();
		bt_le_adv_update_data(ad, ARRAY_SIZE(ad), NULL, 0);
	}
	return 0;
}
