# CopyDetectorGUI

![Screenshot of main window](https://github.com/alexmechanic/CopyDetectorGUI/blob/master/doc/readme_example.png)

## Overview
CopyDetectorGUI is a PyQt UI application for [copydetect](https://github.com/blingenf/copydetect) tool made by [blingenf](https://github.com/blingenf).
It extends usage of copydetect by providing simple and convenient UI to manage copydetect configuration files and running analysis.

## Installation

CopyDetectorGUI requires no classic installation process. To install it, check the [Releases](https://github.com/alexmechanic/CopyDetectorGUI/releases) section and download pre-compiled distribution for desired OS.

## Run from sources

To **run the app** from source code:
- Clone the repository
- Install required dependencies by runnning `python -m pip install -r requirements.txt`
- Execute `./ui2py.sh` to generate form and resource files
- Execute `./src/gui.py` to launch the app

**Note:** Python version 3.6 or greater is required. Older versions might be supported but have not been tested against.

## Build from sources

To **build app distribution** for target (host) OS, run the following commands:
```bash
python -m pip install -r requirements.txt
./ui2py.sh
cd src
./exe_builder.py
```
This will result in creating `exe/OS_TYPE/CopyDetectorGUI` directory containing standalone distribution that can be shipped to users.

**Note:** One can uncomment `--onefile` option in `src/exe_builder.py` to produce one-file binary instead of directory distribution, but it will have significantly slower startup time. For more info, see [How the One-File Program Works in PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html?highlight=one%20file%20works#how-the-one-file-program-works).

## Usage

Basic usage of CopyDetectorGUI should be more or less intuitive, as the options are completely mirrored from [copydetect CLI options](https://github.com/blingenf/copydetect/blob/master/README.md#configuration-options).

**Note:** Configuration files created and saved using CopyDetectorGUI are completely compatible with native copydetect CLI. To run analysis using such files, use `copydetect -c` option.
