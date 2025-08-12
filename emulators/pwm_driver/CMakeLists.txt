# Add executable
add_executable(pwm_driver
        pwm_driver.c
        )

# pull in common dependencies and additional i2c hardware support
target_link_libraries(pwm_driver pico_pwm_driver
    hardware_i2c
    pico_stdlib
    )

# create map/bin/hex file etc.
pico_add_extra_outputs(pwm_driver)



