import subprocess
import os
import argparse
import serial
import json
from time import sleep
import threading
import sys

# Set up argument parsing
parser = argparse.ArgumentParser(
                    prog = 'auto-tester',
                    description = 'Specify the DUT port, buddy port and either a json with tests inside, \
                        or the path to a build folder containing some .elf files you would like to test \
                        The script will automatically open out all folders \
                        and locate any .elf files to test, and puts them in a .json where you can specify \
                        success strings and buddy files.')

parser.add_argument('--dut', required=True)
parser.add_argument('--buddy', required=True)
parser.add_argument('--tests', required=True)

args = parser.parse_args()

print(f"DUT port selected: {args.dut}\nBuddy port selected: {args.buddy}\nTest file selected: {args.tests}")

# After flashing the DUT, wait this long before checking for success strings
timeout = 3

captured_msgs = []

# For stopping the thread
stop = threading.Event()

# For each dictionary in test_data, load the appropriate elfs onto dut and buddy and check for success strings
def main():
    global captured_msgs

    dut_target_set = True
    failed_status = False

    # Initialise results json
    with open("results.json", "w") as file:
        json.dump(["RESULTS:"], file, indent=4) 

    # Load test_files from specified json
    test_file_path = os.path.expanduser(args.tests)
    with open(test_file_path, "r") as file:
        test_data = json.load(file) 
    
    for test in test_data:
        test["dut_file"] = os.path.expanduser(test["dut_file"])
        test["buddy_file"] = os.path.expanduser(test["buddy_file"])
    
    for element in test_data:
        # Announce test name
        print('-----', element["test_name"], '-----')
        print(element["dut_file"])

        # If there is a buddy file specified (e.g an i2c emulator), switch target and flash the elf
        if element["buddy_file"] != 'NULL':
            set_target('buddy')
            dut_target_set = False
            result = subprocess.run(f'~/pico/openocd/src/openocd \
                                    -s ~/pico/openocd/tcl \
                                    -f interface/cmsis-dap.cfg \
                                    -f target/rp2350.cfg \
                                    -c "adapter speed 5000; \
                                    program {element["buddy_file"]} \
                                    verify reset exit"', \
                                    capture_output = True, text = True, shell = True)

            print('\n'.join(result.stderr.splitlines()[-5:]))
    
        # Set target to dut if not already dut
        if dut_target_set == False:
            set_target('dut')
            dut_target_set = True

        # Flash elf onto DUT
        result = subprocess.run(f'~/pico/openocd/src/openocd \
                                -s ~/pico/openocd/tcl \
                                -f interface/cmsis-dap.cfg \
                                -f target/rp2350.cfg \
                                -c "adapter speed 5000; \
                                program {element["dut_file"]} \
                                verify reset exit"', \
                                capture_output = True, text = True, shell = True)

        print('\n'.join(result.stderr.splitlines()[-5:-1]))
        open_ocd_result = ('\n'.join(result.stderr.splitlines()[-5:-1]))

        # Allow timeout seconds for test files to run before checking for success strings
        sleep(timeout)
        print(captured_msgs)

        if check_for_string(captured_msgs, element):
            print("TEST SUCCESFUL")
            write_json(f"Test {element['dut_file']} succeeded with output {captured_msgs}. Programming result: {open_ocd_result}", "results.json")
        else:
            print("TEST FAILED")
            write_json(f"Test {element['dut_file']} failed with output {captured_msgs}. Programming result: {open_ocd_result}", "results.json")
            failed_status=True

        # Empty list for next test
        captured_msgs = []
        sleep(1)

    # Join threads before finishing
    stop.set()
    thread.join()

    # Exit with 1 or 0 so github knows if workflow failed/passes
    if failed_status == True:
        print("One or more tests failed! See results.json for more info.")
        sys.exit(1)
    else:
        print("All tests passes! See results.json for logges outputs.")
        sys.exit(0)


# Function reads list and checks for specified success string
# Returns true if success string in list, else false
def check_for_string(msg_list, element):
    #Some tests dont have any prints so just return true
    if len(msg_list) == 0 and element["success_string"] == 'None':
        return True
    
    for item in msg_list:
        if bytes(element['success_string'], 'utf-8') in item:
            print(f"Found success string {element['success_string']} in msg_list")
            return True
    return False 

# Function for setting target device (either dut or buddy)
def set_target(target):
    target_result = subprocess.run(["cargo", "run", "target", target], cwd = "/home/louis/testing/testctl", capture_output = True, text = True)
    print(target_result.stdout)

# Function for adding results to json
def write_json(new_data, filename):
    with open(filename, 'r+') as file:
        file_data = json.load(file)
        file_data.append(new_data)

        file.seek(0)

        json.dump(file_data, file, indent=4)

# Serial port reading 
dut_port = serial.Serial(port = f"/dev/{args.dut}", baudrate = 115200)
buddy_port = serial.Serial(port = f"/dev/{args.buddy}", baudrate = 115200)

def ReceiveThread():
    global captured_msgs
    while not stop.is_set():
        if dut_port.inWaiting() > 0: # number of bytes in input buffer > 1
            dut_msg = dut_port.readline()
            captured_msgs.append(dut_msg)
        elif buddy_port.inWaiting() > 0:
            buddy_msg = buddy_port.readline()
            captured_msgs.append(buddy_msg)
        else:    
            sleep(0.1)

thread = threading.Thread(target=ReceiveThread)
thread.start()

main()