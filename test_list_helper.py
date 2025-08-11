import subprocess
import os
import argparse
import serial
import json

# Set up argument parsing
parser = argparse.ArgumentParser(
                    prog = 'test_list_helper',
                    description =  'Specify the path to your local build folder of the repository under test \
                                    and the helper will generate a json generated.json which you can copy \
                                    into the repo you want the runner to test.')

parser.add_argument('--root', required=True)

args = parser.parse_args()

print(f"Root selected: {args.root}")

def main():
    build_path = os.path.expanduser(args.root)
    load_json(build_path)

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
        tests.append({"dut_file": path, "buddy_file": "NULL", "success_string": "", "test_name": ""})

    json_tests = json.dumps(tests, indent=4)

    # Load files into json
    with open("generated.json", "w") as file:
        file.write(json_tests)

main()