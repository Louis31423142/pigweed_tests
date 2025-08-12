/**
 * Copyright (c) 2020 Raspberry Pi (Trading) Ltd.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <stdio.h>

#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/clocks.h"

// This emulator drives a PWM output at a range of duty cycles
const uint OUTPUT_PIN = 12;

const float test_duty_cycles[] = {
        0.f,
        0.1f,
        0.5f,
        0.9f,
        1.f
};

int main() {
    stdio_init_all();

    // Configure PWM slice and set it running
    const uint count_top = 1000;
    pwm_config cfg = pwm_get_default_config();
    pwm_config_set_wrap(&cfg, count_top);
    pwm_init(pwm_gpio_to_slice_num(OUTPUT_PIN), &cfg, true);
    gpio_set_function(OUTPUT_PIN, GPIO_FUNC_PWM);

    // For each of our test duty cycles, drive the output pin at that level
    for (uint i = 0; i < count_of(test_duty_cycles); ++i) {
        float output_duty_cycle = test_duty_cycles[i];
        pwm_set_gpio_level(OUTPUT_PIN, (uint16_t) (output_duty_cycle * (count_top + 1)));
        float measured_duty_cycle = measure_duty_cycle(MEASURE_PIN);
        printf("Output duty cycle = %.1f%%", output_duty_cycle * 100.f);
        sleep_ms(100);
    }
}