# Add executable
add_executable(i2c_slave
        i2c_slave.c
        )

# pull in common dependencies and additional i2c hardware support
target_link_libraries(i2c_slave pico_i2c_slave
    hardware_i2c
    pico_stdlib
    )

# create map/bin/hex file etc.
pico_add_extra_outputs(i2c_slave)

target_compile_definitions(i2c_slave PRIVATE PICO_DEFAULT_UART_TX_PIN=16)

