#!/usr/bin/python

import argparse
import glob
import os
import re
import secrets
import shlex
import shutil
import subprocess

parser = argparse.ArgumentParser()
# Allow empty default, which uses the default copr user
parser.add_argument("copr", help="Copr user/@group where the testing Copr \
should be created")
parser.add_argument("url", help="Link to the PR that should be impact checked. \
Eg, https://src.fedoraproject.org/rpms/<package name>/pull-request/<PR \
number>.patch")
parser.add_argument("--chroot", default="fedora-rawhide-x86_64", help="What chroot \
should be used in the testing Copr, the default is fedora-rawhide-x86_64")
args = parser.parse_args()

def repoquery(*args, **kwargs):
    cmd = ['repoquery', '--repo=rawhide', '--repo=rawhide-source']
    if args:
        cmd.extend(args)
    for option, value in kwargs.items():
        cmd.append(f'--{option}')
        if value is not True:
            cmd.append(value)
    proc = subprocess.run(cmd,
                          text=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL,
                          check=True)
    return proc.stdout.splitlines()

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

# add date&time to the copr in addition to the uuid to make it easier to identify, and make collisions extremely unlikely (for long running CI for example)
uuid = secrets.token_hex(4)
new_copr = f"copr-cli create {args.copr}/{package_name}-{uuid} --chroot {args.chroot}"
subprocess.run(shlex.split(new_copr))

fedpkg_srpm = "fedpkg --release rawhide srpm"
subprocess.run(shlex.split(fedpkg_srpm))

copr_build = f"copr-cli build {args.copr}/{package_name}-{uuid} {glob.glob('*.src.rpm')[0]}"
subprocess.run(shlex.split(copr_build))

provides = repoquery(provides=package_name)
deps = []
for pkg in provides:
    [deps.append(x) for x in repoquery(whatrequires=pkg.split(' ')[0], recursive=True)]

for pkg in list(set([x for x in deps if "src" in x])):
    copr_build = f"copr build-distgit {args.copr}/{package_name}-{uuid} --nowait --name {pkg.rsplit('-', 2)[0]}"
    subprocess.run(shlex.split(copr_build))

# Clean up, remove working directory
shutil.rmtree(path)

# Next steps?: Evaluation of failed builds, rebuilding in a testing copr
