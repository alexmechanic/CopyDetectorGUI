#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Executable builder
#

import PyInstaller.__main__, sys, os
from distutils.dir_util import remove_tree

NAME = u'CopyDetectorGUI'

outdir = '../exe'
if sys.platform == "win32":
    outdir += "/win32"
elif sys.platform == "linux":
    outdir += "/linux"
elif sys.platform == "darwin":
    outdir += "/macos"

if __name__ == '__main__':
    print ("Building executable...", end='')
    sys.stdout.flush()
    PyInstaller.__main__.run([
        '--name=%s' % NAME,
        # '--onefile',
        '--windowed',
        '--distpath=' + outdir,
        '--collect-data', 'copydetect',
        '--add-data', '../README.md' + os.pathsep + '.',
        '--clean',
        '--noconfirm',
        '--log-level=CRITICAL',
        '--icon=./ui/icon.ico',
        'gui.py',
    ])
    remove_tree("build")
    os.remove(NAME + ".spec")
    print("Done.\n")
