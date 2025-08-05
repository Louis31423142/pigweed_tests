import subprocess
import os
import argparse
import serial
import json
from time import sleep

# define an attempt limit for every programme
# this might be better included in the json per programme
tries = 10

# Set up argument parsing
# Unused currently, but might be useful
parser = argparse.ArgumentParser(
                    prog='auto-test',
                    description='run tests from json',)

parser.add_argument('--dut')
parser.add_argument('--buddy')

args = parser.parse_args()
print('Arguments:', args.dut, args.buddy)

path_list = [{'dut_file': 'hello_world/serial/hello_serial.elf',
                'buddy_file': 'NULL',
                'success_string': 'Hello, world!\r\n',
                'test_name': 'hello_serial'},
            {'dut_file': 'blink/blink.elf',
                'buddy_file': 'NULL',
                'success_string': '',
                'test_name': 'Blink test'}           
            ]

json_path_list = json.dumps(path_list)

# Load files into json
with open("files.json", "w") as file:
    file.write(json_path_list)

# Read files for testing from files.json
with open("files.json", "r") as file:
    data = json.load(file)

for element in data:
    print(element["dut_file"])

# For each dictionary in data, load the appropriate elfs onto dut and buddy
def main():
    for element in data:
        # Announce test name
        print('-----', element["test_name"], '-----')

        # Set target to dut
        set_target('dut')

        # Flash elf onto DUT
        result = subprocess.run(f'~/pico/openocd/src/openocd -s ~/pico/openocd/tcl -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000; program /home/louis/pico/pico_examples/build/{element["dut_file"]} verify reset exit"', capture_output = True, text = True, shell = True)
        '''
        print(result.stdout)
        print(result.stderr)
        '''

        # If there is a buddy file specified (e.g an i2c emulator), switch target and flash the elf
        if element["buddy_file"] != 'NULL':
            set_target('buddy')
            result = subprocess.run(f'~/pico/openocd/src/openocd -s ~/pico/openocd/tcl -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000; program /home/louis/pico/pico_examples/build/{element["buddy_file"]} verify reset exit"', capture_output = True, text = True, shell = True)
            '''
            print(result.stdout)
            print(result.stderr)
            '''

        # Now wait for either timeout or success
        check_for_string(tries, f'/dev/{args.dut}', element)


# Function reads UART and checks for specified success string
def check_for_string(attempt_limit, port, element):
    line = b''
    attempts = 0

    expected = bytes(element['success_string'], 'utf-8')
    print("expected:", expected)
    while True:
        with serial.Serial(port, 115200, timeout=1) as ser:
            line = ser.readline()
            print('ACM1', line)
            attempts += 1
            sleep(1)
        if line == expected:
            print("Success!")
            break
        elif attempts == attempt_limit:
            print("Attempt limit reached")
            break

# Function for setting target device (either dut or buddy)
def set_target(target):
    target_result = subprocess.run(["cargo", "run", "target", target], cwd = "/home/louis/testing/testctl", capture_output = True, text = True)
    print(target_result.stdout)


main()