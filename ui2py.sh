#!/bin/bash
#
# Copyright (c) 2022 Gerasimov Alexander <samik.mechanic@gmail.com>
#

pyuic5 src/ui/mainwindow.ui -o src/mainform.py
# force-align Analyze button center of grid
sed -i "" "s/addWidget(self.run_button, 5, 0, 1, 4)/addWidget(self.run_button, 5, 0, 1, 4, alignment=QtCore.Qt.AlignCenter)/g" src/mainform.py
pyrcc5 src/ui/resource.rc -o src/resource.py
