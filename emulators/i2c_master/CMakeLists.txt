add_executable(i2c_master
        i2c_master.c
        )

# pull in common dependencies and additional i2c hardware support
target_link_libraries(i2c_master pico_i2c_slave
    hardware_i2c
    pico_stdlib
    )

# create map/bin/hex file etc.
pico_add_extra_outputs(i2c_master)

target_compile_definitions(i2c_master PRIVATE PICO_DEFAULT_UART_TX_PIN=12)
