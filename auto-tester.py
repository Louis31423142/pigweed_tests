import subprocess
import os
import argparse
import serial
import json
from time import sleep
import threading

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

# Required group so user has to submit either a root or a tests json
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--root')
group.add_argument('--tests')

args = parser.parse_args()

print(f"DUT port selected: {args.dut}\nBuddy port selected: {args.buddy}")

if args.root != None:
    print(f"Root path selected: {args.root}")
else:
    print(f"Tests file selected: {args.tests}")

# After flashing the DUT, wait this long before checking for success strings
timeout = 3

captured_msgs = []

# For stopping the thread
stop = threading.Event()
# For each dictionary in test_data, load the appropriate elfs onto dut and buddy and check for success strings
def main():
    global captured_msgs

    # Initialise results json
    with open("results.json", "w") as file:
        json.dump(["RESULTS:"], file, indent=4) 

    # If the user passed a root directory to expand into files, create the json based on this
    if args.root != None:
        load_json(args.root)
        with open("tests.json", "r") as file:
            test_data = json.load(file)

    # Otherwise, load test_files from specified json
    else:
       with open(args.tests, "r") as file:
            test_data = json.load(file) 
    
    for element in test_data:
        # Announce test name
        print('-----', element["test_name"], '-----')
        print(element["dut_file"])

        # If there is a buddy file specified (e.g an i2c emulator), switch target and flash the elf
        if element["buddy_file"] != 'NULL':
            set_target('buddy')
            result = subprocess.run(f'~/pico/openocd/src/openocd \
                                    -s ~/pico/openocd/tcl \
                                    -f interface/cmsis-dap.cfg \
                                    -f target/rp2350.cfg \
                                    -c "adapter speed 5000; \
                                    program /home/louis/auto-tests/emulators/build/{element["buddy_file"]} \
                                    verify reset exit"', \
                                    capture_output = True, text = True, shell = True)

            print('\n'.join(result.stderr.splitlines()[-5:]))

        # Set target to dut
        set_target('dut')

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

        # Allow timeout seconds for test files to run before checking for success strings
        sleep(timeout)

        if check_for_string(captured_msgs, element):
            print("TEST SUCCESFUL")
            write_json(f"Test {element['dut_file']} succeeded", "results.json")
        else:
            print("TEST FAILED")
            write_json(f"Test {element['dut_file']} failed.", "results.json")

        # Empty list for next test
        captured_msgs = []
        sleep(1)

    # Join threads before finishing
    stop.set()
    thread.join()

    print("Finished testing")


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

# Function for loading json with all .elf files contained within some root directory
# Creates tests.json
def load_json(root):
    # Expand root to full path
    path = os.path.expanduser(f"{root}")

    elf_path_list = []
    dir_path_list = [path]

    while True:
        elf_changes = 0
        dir_changes = 0
        temp_list = []

        # Try to get the contents from every directory in dir_list
        for path in dir_path_list:
            try:
                expanded_list = os.listdir(path)
                for item in expanded_list:
                    temp_list.append(f"{path}/{item}")
            except:
                pass

        # Split the paths contained in temp_list into either directories or .elfs 
        for path in temp_list:
            if os.path.isdir(path) and path not in dir_path_list:
                dir_path_list.append(path)
                dir_changes += 1
            elif path.endswith(".elf") and path not in elf_path_list:
                elf_path_list.append(path)
                elf_changes += 1

        # If we havent added to directories list or .elf list, must be done searching
        if elf_changes == 0 and dir_changes == 0:
            break

    tests = []
    for path in elf_path_list:
        tests.append({"dut_file": path, "buddy_file": "NULL", "success_string": "", "test_name": "TEST"})

    json_tests = json.dumps(tests, indent=4)

    # Load files into json
    with open("tests.json", "w") as file:
        file.write(json_tests)

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