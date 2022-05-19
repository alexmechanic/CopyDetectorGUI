#!/bin/bash
#
# Copyright (c) 2022 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Executable builder main script
#

echo -n "Creating build environment..."
python3 -m venv build_env
echo "done."
source ./build_env/bin/activate
echo -n "Installing requirements..."
python3 -m pip install -r ../requirements.txt &> /dev/null
echo "done."
echo -n "Building distribution..."
python3 exe_builder.py  &> /dev/null
echo "done."
echo -n "Cleaning up..."
deactivate
rm -rf build_env
echo "done."
