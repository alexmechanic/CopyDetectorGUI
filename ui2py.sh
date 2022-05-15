#!/bin/bash
#
# Copyright (c) 2022 Gerasimov Alexander <samik.mechanic@gmail.com>
#

pyuic5 src/ui/mainwindow.ui -o src/mainform.py
pyrcc5 src/ui/resource.rc -o src/resource.py
