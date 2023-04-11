#!/usr/bin/python

import argparse
import os
import re
import shlex
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("url", help="Link to the PR that should be impact checked. \
Eg, https://src.fedoraproject.org/rpms/<package name>/pull-request/<PR \
number>.patch")
args = parser.parse_args()

try:
    package_name = re.search("(?<=rpms\/)(.*)(?=\/pull-request)", args.url)
    path = f"/tmp/{package_name.group(0)}"
except AttributeError:
    print("Given URL address doesn't match expected format, see --help.")
    exit(1)

# Create working directory
os.mkdir(path)

wget = f"wget -P {path} {args.url}"
subprocess.run(shlex.split(wget))

# Clean up, remove working directory
shutil.rmtree(path)

