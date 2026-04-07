import os
import sys

user_input = sys.argv[1]

# Dangerous
os.system(user_input)

# More dangerous
import subprocess
subprocess.Popen(user_input, shell=True)