# Generated Cmake Pico project file
cmake_minimum_required(VERSION 3.13)

# Pull in SDK (must be before project)
include(pico_sdk_import.cmake)

project(emulators C CXX ASM)

# Initialise the Raspberry Pi Pico SDK
pico_sdk_init()

# Add the i2c emulator
add_subdirectory(i2c_slave)
add_subdirectory(spi_emulator)