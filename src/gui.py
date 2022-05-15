#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Gerasimov Alexander <samik.mechanic@gmail.com>
#

import sys, os, json, platform, webbrowser, copy, re

from construct import Switch
from mainform import Ui_MainWindow
import resource
# from parse_report import RunAnalysis_GUI
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class Editor(QMainWindow): # класс, генерирующий основное окно приложения
    src_dir = None
    src_users = None
    dst_file = None
    SettingsFileName = None

    def __init__(self):
        super(Editor, self).__init__()
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        self.saved_settings = {
            "test_directories": [],
            "reference_directories" : [],
            "boilerplate_directories" : [],
            "extensions" : [],
            "noise_threshold" : 25,
            "guarantee_threshold" : 30,
            "display_threshold" : 33,
            "same_name_only" : False,
            "ignore_leaf" : False,
            "disable_filtering" : False,
            "disable_autoopen" : False,
            "truncate" : False,
            "out_file" : os.getcwd(),
        }
        self.current_settings = copy.deepcopy(self.saved_settings)
        self.SettingsFileName = os.getcwd() + "/" + "sample.cfg"
        self.LoadConfigFile()
        self.ui.run_button.setIcon(QIcon(":/icons/run"))
        self.UpdateUI()
        # connect actions & buttons
        self.ui.actionOpen_configuration.triggered.connect(self.ChooseConfigFile)
        # add/remove from list buttons
        self.ui.test_dirs_button_add.clicked.connect(self.AddDir_test)
        self.ui.ref_dirs_button_add.clicked.connect(self.AddDir_ref)
        self.ui.bp_dirs_button_add.clicked.connect(self.AddDir_bp)
        self.ui.test_dirs_button_remove.clicked.connect(self.DelDir_test)
        self.ui.ref_dirs_button_remove.clicked.connect(self.DelDir_ref)
        self.ui.bp_dirs_button_remove.clicked.connect(self.DelDir_bp)
        # extensions checkboxes
        self.ui.extensions_c_source_checkbox.stateChanged.connect(self.EditExt_c)
        self.ui.extensions_c_header_checkbox.stateChanged.connect(self.EditExt_h)
        self.ui.extensions_python_checkbox.stateChanged.connect(self.EditExt_py)
        self.ui.extensions_other_checkbox.stateChanged.connect(self.EditExt_other_enable)
        # self.ui.extensions_other_edit.textChanged.connect(self.EditExt_other)

    def LoadConfigFile(self):
        if os.path.isfile(self.SettingsFileName):
            with open(self.SettingsFileName, "r") as settings_file:
                settings = json.load(settings_file)
                for key in settings.keys():
                    if key != "display_threshold":
                        self.current_settings[key] = settings[key]
                    else:
                        self.current_settings[key] = int(settings[key]*100)
                # refresh change state
                self.saved_settings = copy.deepcopy(self.current_settings)
            self.setWindowTitle("CopyDetect UI - " + self.SettingsFileName.split('/')[-1])

    def ChooseConfigFile(self):
        self.SettingsFileName, _ = QFileDialog.getOpenFileName(self, self.SettingsFileName, "Выбор сохраненной конфигурации", os.path.expanduser("~"), "Настройки CopyDetect (*.cfg *.json)")
        self.LoadConfigFile()
        self.UpdateUI()

    def UpdateUI(self):
        model = QStandardItemModel(self.ui.test_dirs_list)
        for dir in self.current_settings["test_directories"]:
            item = QStandardItem(QIcon(":/icons/folder"), dir)
            model.appendRow(item)
        self.ui.test_dirs_list.setModel(model)
        model = QStandardItemModel(self.ui.test_dirs_list)
        for dir in self.current_settings["reference_directories"]:
            item = QStandardItem(QIcon(":/icons/folder"), dir)
            model.appendRow(item)
        self.ui.ref_dirs_list.setModel(model)
        model = QStandardItemModel(self.ui.test_dirs_list)
        for dir in self.current_settings["boilerplate_directories"]:
            item = QStandardItem(QIcon(":/icons/folder"), dir)
            model.appendRow(item)
        self.ui.bp_dirs_list.setModel(model)
        # manage extensions list into checkboxes and 'other' list
        if 'c' in self.current_settings["extensions"] or 'cpp' in self.current_settings["extensions"]:
            if 'c' in self.current_settings["extensions"]:
                self.current_settings["extensions"].insert(self.current_settings["extensions"].index('c'), 'cpp')
                self.current_settings["extensions"].insert(self.current_settings["extensions"].index('c'), 'cc')
            elif 'cpp' in self.current_settings["extensions"]:
                self.current_settings["extensions"].insert(self.current_settings["extensions"].index('cpp'), 'c')
                self.current_settings["extensions"].insert(self.current_settings["extensions"].index('cpp'), 'cc')
            else:
                self.current_settings["extensions"].insert(self.current_settings["extensions"].index('cc'), 'c')
                self.current_settings["extensions"].insert(self.current_settings["extensions"].index('cc'), 'cpp')
        self.ui.extensions_c_source_checkbox.setChecked('c' in self.current_settings["extensions"] or 'cpp' in self.current_settings["extensions"])
        if 'h' in self.current_settings["extensions"] or 'hpp' in self.current_settings["extensions"]:
            if 'h' in self.current_settings["extensions"]:
                self.current_settings["extensions"].insert(self.current_settings["extensions"].index('h'), 'hpp')
            else:
                self.current_settings["extensions"].insert(self.current_settings["extensions"].index('hpp'), 'h')
        self.ui.extensions_c_header_checkbox.setChecked('h' in self.current_settings["extensions"] or 'hpp' in self.current_settings["extensions"])
        self.ui.extensions_python_checkbox.setChecked('py' in self.current_settings["extensions"])
        other_types = []
        for ext in self.current_settings["extensions"]:
            if ext not in ['c', 'cpp', 'h', 'hpp', 'py']:
                other_types.append(ext)
        if len(other_types):
            self.ui.extensions_other_checkbox.setChecked(True)
            self.ui.extensions_other_edit.setText(",  ".join(ex for ex in other_types))
            self.ui.extensions_other_edit.setEnabled(True)
        self.ui.thresholds_noise_spinbox.setValue(self.current_settings["noise_threshold"])
        self.ui.thresholds_guarantee_spinbox.setValue(self.current_settings["guarantee_threshold"])
        self.ui.thresholds_display_spinbox.setValue(self.current_settings["display_threshold"])
        self.ui.additional_samename_checkbox.setChecked(self.current_settings["same_name_only"])
        self.ui.additional_sameleaf_checkbox.setChecked(self.current_settings["ignore_leaf"])
        self.ui.additional_filtering_checkbox.setChecked(self.current_settings["disable_filtering"])
        self.ui.additional_autoopen_checkbox.setChecked(self.current_settings["disable_autoopen"])
        self.ui.additional_truncate_checkbox.setChecked(self.current_settings["truncate"])
        self.ui.output_location_edit.setText(self.current_settings["out_file"] + "/report.html")
        self.ui.run_button.setEnabled(len(self.current_settings["test_directories"]) and \
                                      len(self.current_settings["reference_directories"]) and \
                                      len(self.current_settings["boilerplate_directories"]) and \
                                      os.path.isdir(self.current_settings["out_file"]))
        # set unsaved state for window title
        print(self.saved_settings)
        print(self.current_settings)
        if self.current_settings != self.saved_settings:
            if self.windowTitle()[-1] != '*':
                self.setWindowTitle(self.windowTitle() + '*')
        else:
            if self.windowTitle()[-1] == '*':
                self.setWindowTitle(self.windowTitle()[:-1])

    # add button connection redirection funcs
    def AddDir_test(self):
        self.AddDir("test_directories")
    def AddDir_ref(self):
        self.AddDir("reference_directories")
    def AddDir_bp(self):
        self.AddDir("boilerplate_directories")
    # main one
    def AddDir(self, type):
        dir = QFileDialog.getExistingDirectory(self, "Выбор каталога", os.path.expanduser("~"))
        if dir not in self.current_settings[type]:
            self.current_settings[type].append(dir)
        self.UpdateUI()

    # remove button connection redirection funcs
    def DelDir_test(self):
        self.DelDir("test_directories")
    def DelDir_ref(self):
        self.DelDir("reference_directories")
    def DelDir_bp(self):
        self.DelDir("boilerplate_directories")
    # main one
    def DelDir(self, type):
        if type == "test_directories":
            to_del = self.ui.test_dirs_list.currentIndex().data(Qt.DisplayRole)
        elif type == "reference_directories":
            to_del = self.ui.ref_dirs_list.currentIndex().data(Qt.DisplayRole)
        else: # bp dir
            to_del = self.ui.bp_dirs_list.currentIndex().data(Qt.DisplayRole)
        if to_del is not None:
            self.current_settings[type].remove(to_del)
        self.UpdateUI()

    def EditExt_c(self):
        self.EditExt(['cpp'], self.ui.extensions_c_source_checkbox.isChecked())
    def EditExt_h(self):
        self.EditExt(['hpp'], self.ui.extensions_c_header_checkbox.isChecked())
    def EditExt_py(self):
        self.EditExt(['py'], self.ui.extensions_python_checkbox.isChecked())
    def EditExt_other_enable(self):
        enable = self.ui.extensions_other_checkbox.isChecked()
        self.ui.extensions_other_edit.setEnabled(enable)
        # force-load saved settings
        if enable:
            self.current_settings["extensions"] = copy.deepcopy(self.saved_settings["extensions"])
            self.UpdateUI()
        self.EditExt_other()
        self.UpdateUI()
    # TODO: dont forget to check for text changed on close and before Analyze run!!!
    #  I cannot apply changes every time the single char changed here!
    #  Just call EditExt_other(), it does all the needed work
    def EditExt_other(self):
        enable = self.ui.extensions_other_checkbox.isChecked()
        exts = re.sub('[ *.]', '', self.ui.extensions_other_edit.text()).split(',')
        print(exts)
        self.EditExt(exts, enable)
    def EditExt(self, exts, enable=True):
        for ext in exts:
            if enable:
                if ext not in self.current_settings["extensions"]:
                    print("add", ext)
                    self.current_settings["extensions"].append(ext)
            else:
                if ext in self.current_settings["extensions"]:
                    print("remove", ext)
                    self.current_settings["extensions"].remove(ext)
        self.UpdateUI()
    

    def closeEvent(self, event):
        # save settings
        # TODO add check for changes and prompt
        # with open(os.getcwd() + "/" + self.SettingsFileName, "w") as settings_file:
        #     json.dump(settings, settings_file)
        #     settings_file.close()
        event.accept()

    def OpenHelp(self):
        if platform.system() == 'Darwin':
            client = webbrowser.get('safari')
            client.open_new_tab(os.getcwd() + "/README.md")
        else:
            webbrowser.open_new_tab(os.getcwd() + "/README.md")

    def About(self):
        QMessageBox.information(self, u"О программе", \
            u"DESCRIPTION\n\nАвтор:\nГерасимов Александр\n<samik.mechanic@gmail.com>")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Editor()
    ex.show()
    # вывод окна на передний план
    ex.raise_()
    sys.exit(app.exec())
