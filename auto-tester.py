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
parser.add_argument('--root')

args = parser.parse_args()
print('Arguments:', args.dut, args.buddy)

captured_msgs = []

# For each dictionary in data, load the appropriate elfs onto dut and buddy
def main():
    global captured_msgs

    # If the user passed a root directory to expand into files, create the json based on this
    if args.root != None:
        load_json(args.root)
    
    # Read files for testing from files.json
    with open("files.json", "r") as file:
        test_data = json.load(file)

    for element in test_data:
        # Announce test name
        print('-----', element["test_name"], '-----')
        print(element["dut_file"])

        # If there is a buddy file specified (e.g an i2c emulator), switch target and flash the elf
        if element["buddy_file"] != 'NULL':
            set_target('buddy')
            result = subprocess.run(f'~/pico/openocd/src/openocd -s ~/pico/openocd/tcl -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000; program /home/louis/auto-tests/emulators/build/{element["buddy_file"]} verify reset exit"', capture_output = True, text = True, shell = True)

            #print(result.stdout)
            #print(result.stderr)


        # Set target to dut
        set_target('dut')

        # Flash elf onto DUT
        result = subprocess.run(f'~/pico/openocd/src/openocd -s ~/pico/openocd/tcl -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000; program {element["dut_file"]} verify reset exit"', capture_output = True, text = True, shell = True)

        #print(result.stdout)
        #print(result.stderr)

        # Allow timeout seconds for test files to run before checking for success strings
        sleep(timeout)
        #print(captured_msgs)

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
    #Some tests dont have any prints so just return true
    if len(msg_list) == 0 and element["success_string"] == 'None':
        return True
    
    for item in msg_list:
        if bytes(element['success_string'], 'utf-8') in item:
            print(f"Found success string {item} in msg_list")
            return True
    return False 

# Function for setting target device (either dut or buddy)
def set_target(target):
    target_result = subprocess.run(["cargo", "run", "target", target], cwd = "/home/louis/testing/testctl", capture_output = True, text = True)
    print(target_result.stdout)

# Function for loading json with pico examples .elf files
def load_json(root):
    #expand root to full path
    path = os.path.expanduser(f"{root}")

    file_path_list = []
    dir_path_list = [path]

    for _ in range(3):
        temp_list_2 = []
        for dir in dir_path_list:
            try:
                temp_list = os.listdir(dir)
                for item in temp_list:
                    temp_list_2.append(f"{dir}/{item}")
            except:
                pass

        for item in temp_list_2:
            if item not in dir_path_list:
                dir_path_list.append(item)
                if item.endswith(".elf"):
                    file_path_list.append(item)

    data = []
    for path in file_path_list:
        data.append({"dut_file": path, "buddy_file": "NULL", "success_string": "Hello, world!\r\n", "test_name": "TEST"})
    
    json_data = json.dumps(data, indent=4)

    # Load files into json
    with open("new_files.json", "w") as file:
        file.write(json_data)

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