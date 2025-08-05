# Add executable
add_executable(i2c
        i2c_device.c
        )

# pull in common dependencies and additional i2c hardware support
target_link_libraries(i2c pico_i2c_slave
    hardware_i2c
    pico_stdlib
    )

# create map/bin/hex file etc.
pico_add_extra_outputs(i2c)