import subprocess
import os
import argparse
import serial
import json
from time import sleep
import threading

# define an attempt limit for every programme
# this might be better included in the json per programme
timeout = 3

# Set up argument parsing
parser = argparse.ArgumentParser(
                    prog='auto-test',
                    description='run tests from json',)

parser.add_argument('--dut')
parser.add_argument('--buddy')

args = parser.parse_args()
print('Arguments:', args.dut, args.buddy)

captured_msgs = []

'''
path_list = [{'dut_file': 'hello_world/serial/hello_serial.elf',
                'buddy_file': 'NULL',
                'success_string': 'Hello, world!\r\n',
                'test_name': 'HELLO WORLD TEST'}, 
            {'dut_file': 'clocks/detached_clk_peri/clocks_detached_clk_peri.elf',
                'buddy_file': 'NULL',
                'success_string': 'Measuring system clock with frequency counter:13300 kHz\r\n',
                'test_name': 'CLOCK TEST'}, 
            {'dut_file': 'blink/blink.elf',
                'buddy_file': 'NULL',
                'success_string': '',
                'test_name': 'Blink test'}, 
            {'dut_file': 'pio/uart_tx.elf',
                'buddy_file': 'NULL',
                'success_string': 'Hello GPIO IRQ\n',
                'test_name': 'pio uart tx test'},
            {'dut_file': 'gpio/hello_gpio_irq/hello_gpio_irq.elf',
                'buddy_file': 'NULL',
                'success_string': 'Hello GPIO IRQ\n',
                'test_name': 'Hello gpio test'}]

json_path_list = json.dumps(path_list)

# Load files into json
with open("files.json", "w") as file:
    file.write(json_path_list)

# Read files for testing from files.json
with open("files.json", "r") as file:
    data = json.load(file)

for element in data:
    print(element["dut_file"])

'''
# For each dictionary in data, load the appropriate elfs onto dut and buddy
def main():
    global captured_msgs

    # Get a list of all examples
    examples_path = os.path.expanduser("~/pico/clean-examples/dut_build")
    file_path_list = []
    dir_path_list = [examples_path]

    for i in range(3):
        changes = 0
        temp_list_2 = []
        for dir in dir_path_list:
            try:
                temp_list = os.listdir(dir)
                for item in temp_list:
                    temp_list_2.append(f"{dir}/{item}")
                changes += 1
            except:
                print("Not a directory!")

        for item in temp_list_2:
            dir_path_list.append(item)
            if item.endswith(".elf"):
                file_path_list.append(item)

        if changes == 0:
            break

    #print(file_path_list)
    data = []
    n = 0
    for path in file_path_list:
        n += 1
        data.append({"dut_file": path, "buddy_file": "NULL", "success_string": "Hello, world!\r\n", "test_name": f"TEST {n}"})


    for element in data:
        # Announce test name
        print('-----', element["test_name"], '-----')
        print(element["dut_file"])

        # Set target to dut
        set_target('dut')

        # Flash elf onto DUT
        result = subprocess.run(f'~/pico/openocd/src/openocd -s ~/pico/openocd/tcl -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000; program {element["dut_file"]} verify reset exit"', capture_output = True, text = True, shell = True)

        print(result.stdout)
        print(result.stderr)

        # If there is a buddy file specified (e.g an i2c emulator), switch target and flash the elf
        if element["buddy_file"] != 'NULL':
            set_target('buddy')
            result = subprocess.run(f'~/pico/openocd/src/openocd -s ~/pico/openocd/tcl -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000; program /home/louis/pico/clean-examples/buddy_build{element["buddy_file"]} verify reset exit"', capture_output = True, text = True, shell = True)

            #print(result.stdout)
            #print(result.stderr)

        # Allow timeout seconds for test files to run before checking for success strings
        sleep(timeout)
        print(captured_msgs)

        if check_for_string(captured_msgs, element):
            print("TEST SUCCESFUL")
        else:
            print("TEST FAILED")

        # Empty list for next test
        captured_msgs = []
        sleep(1)

# Function reads list and checks for specified success string
# Returns true if success string in list, else false
def check_for_string(msg_list, element):
    for item in msg_list:
        if item == bytes(element['success_string'], 'utf-8'):
            return True
    return False 

# Function for setting target device (either dut or buddy)
def set_target(target):
    target_result = subprocess.run(["cargo", "run", "target", target], cwd = "/home/louis/testing/testctl", capture_output = True, text = True)
    print(target_result.stdout)

# Serial port reading 
dut_port = serial.Serial(port = f"/dev/{args.dut}", baudrate = 115200)
buddy_port = serial.Serial(port = f"/dev/{args.buddy}", baudrate = 115200)

def ReceiveThread():
    global captured_msgs
    while True:
        if dut_port.inWaiting() > 0: # number of bytes in input buffer > 1
            dut_msg = dut_port.readline()
            #print("DUT: ", dut_msg)
            captured_msgs.append(dut_msg)
        elif buddy_port.inWaiting() > 0:
            buddy_msg = buddy_port.readline()
            #print("BUDDY: ", buddy_msg)
            captured_msgs.append(buddy_msg)
        else:    
            sleep(0.1)

threading.Thread(target=ReceiveThread).start()

main()