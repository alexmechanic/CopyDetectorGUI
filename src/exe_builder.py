#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Gerasimov Alexander <samik.mechanic@gmail.com>
#
# Executable builder
#

import PyInstaller.__main__, sys, os
from distutils.dir_util import remove_tree

# имя файла программы
NAME = u'CopyDetectorGUI'

if __name__ == '__main__':
    print ("Building executable...", end='')
    sys.stdout.flush()
    PyInstaller.__main__.run([
        '--name=%s' % NAME,
        # '--onefile',
        '--windowed',
        '--distpath=../exe',
        '--collect-data', 'copydetect',
        '--clean',
        '--noconfirm',
        '--log-level=CRITICAL',
        '--icon=./ui/icon.ico',
        'gui.py',
    ])
    remove_tree("build")
    os.remove(NAME + ".spec")
    print("Done.\n")
