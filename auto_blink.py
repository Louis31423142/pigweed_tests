import subprocess
import os
import argparse
import serial
import json

# Set up argument parsing
parser = argparse.ArgumentParser(
                    prog='auto-test',
                    description='run given programme on selected target',
                    epilog='Text at the bottom of help')

parser.add_argument('--file')
parser.add_argument('--target')

args = parser.parse_args()
print(args.file, args.target)

path_list = [{'dut_file': 'hello_world/usb/hello_usb.elf',
                'buddy_file': 'hello_world/usb/hello_usb.elf',
                'success_strings': ['string1', 'string2'],
                'test_name': 'TEST1'},
            {'dut_file': 'blink/blink.elf',
                'buddy_file': 'blink/blink.elf',
                'success_strings': ['string1', 'string2'],
                'test_name': 'TEST2'}           
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

# Set up pyserial for monitoring UART
# Read every 1 second
port0 = serial.Serial("/dev/ttyACM0", baudrate = 115200, timeout = 1.0)
port1 = serial.Serial("/dev/ttyACM1", baudrate = 115200, timeout = 1.0)

# For each dictionary in data, load the appropriate elfs onto dut and buddy
for element in data:
    # Announce test name
    print('-----', element["test_name"], '-----')

    # Set target to dut
    target_result = subprocess.run(["cargo", "run", "target", "dut"], cwd = "/home/louis/testing/testctl", capture_output = True, text = True)
    print(target_result.stdout)

    # Flash elf onto DUT
    result = subprocess.run(f'~/pico/openocd/src/openocd -s ~/pico/openocd/tcl -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000; program /home/louis/pico/pico_examples/build/{element["dut_file"]} verify reset exit"', capture_output = True, text = True, shell = True)

    print(result.stdout)
    print(result.stderr)

    # Set target to buddy
    target_result = subprocess.run(["cargo", "run", "target", "buddy"], cwd = "/home/louis/testing/testctl", capture_output = True, text = True)
    print(target_result.stdout)

    # Flash elf onto buddy
    result = subprocess.run(f'~/pico/openocd/src/openocd -s ~/pico/openocd/tcl -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000; program /home/louis/pico/pico_examples/build/{element["buddy_file"]} verify reset exit"', capture_output = True, text = True, shell = True)

    print(result.stdout)
    print(result.stderr)




# Now monitor serial
'''
while True:
    rcv0 = port0.read()
    rcv1 = port1.read()
    print("port 0 recieved: ", rcv0)
    print("port 1 recieved: ", rcv1)
'''