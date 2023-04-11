#!/usr/bin/python

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("url", help="Link to the PR that should be impact checked. \
Eg, https://src.fedoraproject.org/rpms/<package name>/pull-request/<PR \
number>.patch")
args = parser.parse_args()

