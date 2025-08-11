# Pigweed automated testing

This code is for automated testing using the pigweed rp2350 Target Board rev 2. 

## Setup

Setup a raspberry pi as a self-hosted github runner attached to your desired repository. Add this repo to the pi. Add a folder runner_build, and clone the repo you want 
to test here.

Add main.yml to your repository workflows making sure to change xxx/xxx.json. The test file xxx.json should be added to your repo, and a template can be generated using test_list_helper.py. 

To use test_list_helper pass a single argument --root which is the location of your build folder on the pi. You will have to build the repo once, and test_list_helper
will seek out any .elf files within and create generated.json in pigweed_tests which can be copied into your repository. Remove any tests you don't want, add names, success strings
and buddy files (if required, eg an i2c emulator). 

Now whenever you push, the runner will go through all the test files in xxx.json and check for the specified success strings. 

The workflow returns an artifact results.json which details the results of each test, any print output and the openocd result.  
