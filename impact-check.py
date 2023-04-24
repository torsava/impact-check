#!/usr/bin/python

import argparse
import os
import re
import secrets
import shlex
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("copr", help="Copr user/@group where the testing Copr \
should be created")
parser.add_argument("url", help="Link to the PR that should be impact checked. \
Eg, https://src.fedoraproject.org/rpms/<package name>/pull-request/<PR \
number>.patch")
parser.add_argument("--chroot", default="fedora-rawhide-x86_64", help="What chroot \
should be used in the testing Copr, the default is fedora-rawhide-x86_64")
args = parser.parse_args()

try:
    package_name = re.search("(?<=rpms\/)(.*)(?=\/pull-request)", args.url).group(0)
    path = f"/tmp/{package_name}"
    pr_number = args.url.split('/')[-1]
except AttributeError:
    print("Given URL address doesn't match expected format, see --help.")
    exit(1)

# Create working directory
os.mkdir(path)

fedpkg = f"fedpkg clone {package_name} {path}"
subprocess.run(shlex.split(fedpkg))

os.chdir(path)

wget = f"wget -P {path} {args.url}"
subprocess.run(shlex.split(wget))

git_apply = f"git apply {pr_number}"
subprocess.run(shlex.split(git_apply))

uuid = secrets.token_hex(4)
new_copr = f"copr-cli create {args.copr}/{package_name}-{uuid} --chroot {args.chroot}"
subprocess.run(shlex.split(new_copr))

# Clean up, remove working directory
shutil.rmtree(path)

