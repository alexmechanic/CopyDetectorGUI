#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Gerasimov Alexander <samik.mechanic@gmail.com>
#

import sys, os, json, platform, webbrowser, copy, re

import resource
from mainform import Ui_MainWindow
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
            "out_file" : os.getcwd() + '/report.html',
        }
        self.current_settings = copy.deepcopy(self.saved_settings)
        # debug value
        # self.SettingsFileName = os.getcwd() + "/" + "sample.cfg"
        self.SettingsFileName = ""
        self.LoadConfigFile()
        self.ui.run_button.setIcon(QIcon(":/icons/run"))
        self.UpdateUI()
        # connect actions & buttons
        self.ui.actionOpen_configuration.triggered.connect(self.OpenConfigFile)
        self.ui.actionSave_configuration.triggered.connect(self.SaveConfigFile)
        self.ui.actionSave_configuration_as.triggered.connect(self.SaveConfigFileAs)
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
        # thresholds spinboxes
        self.ui.thresholds_noise_spinbox.valueChanged.connect(self.EditThres_noise)
        self.ui.thresholds_guarantee_spinbox.valueChanged.connect(self.EditThres_guar)
        self.ui.thresholds_display_spinbox.valueChanged.connect(self.EditThres_disp)
        # additional checkboxes
        self.ui.additional_samename_checkbox.stateChanged.connect(self.EditAdd_samename)
        self.ui.additional_sameleaf_checkbox.stateChanged.connect(self.EditAdd_leaf)
        self.ui.additional_filtering_checkbox.stateChanged.connect(self.EditAdd_filt)
        self.ui.additional_autoopen_checkbox.stateChanged.connect(self.EditAdd_autoopen)
        self.ui.additional_truncate_checkbox.stateChanged.connect(self.EditAdd_truncate)
        # out file selection button
        self.ui.output_location_select_button.clicked.connect(self.SelectOutFile)
        # out file full path edit change
        self.ui.output_location_edit.textChanged.connect(self.ChangeOutFilePath)

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
            self.setWindowTitle("CopyDetect UI - " + self.SettingsFileName)

    def OpenConfigFile(self):
        initdir = os.path.expanduser("~") \
            if self.SettingsFileName == "" or not os.path.isfile(self.SettingsFileName) \
            else self.SettingsFileName
        file, _ = QFileDialog.getOpenFileName(self, "Open configuration", initdir, "CopyDetect settings (*.json)")
        if file == "" or not os.path.isfile(file):
            return
        self.SettingsFileName = file
        self.LoadConfigFile()
        self.UpdateUI()

    def SaveConfigFile(self):
        if not self.CheckForSettingsChange():
            return
        if self.SettingsFileName == "" or not os.path.isfile(self.SettingsFileName):
            self.SaveConfigFileAs()
        else:
            with open(self.SettingsFileName, "w") as settings_file:
                # back-workaround for 'display_threshold' value
                settings = copy.deepcopy(self.current_settings)
                settings["display_threshold"] = float(settings["display_threshold"]/100)
                json.dump(settings, settings_file, indent=4, separators=(",", ": "))
            self.saved_settings = copy.deepcopy(self.current_settings)
            self.CheckForSettingsChange()

    def SaveConfigFileAs(self):
        if not self.CheckForSettingsChange():
            return
        initdir = os.path.expanduser("~") + "/config.json" \
            if self.SettingsFileName == "" or not os.path.isfile(self.SettingsFileName) \
            else self.SettingsFileName
        file, _ = QFileDialog.getSaveFileName(self, "Save new configuration", initdir, "CopyDetect settings (*.json)")
        if file == "":
            return
        self.SettingsFileName = file
        with open(self.SettingsFileName, "w") as settings_file:
            # back-workaround for 'display_threshold' value
            settings = copy.deepcopy(self.current_settings)
            settings["display_threshold"] = float(settings["display_threshold"]/100)
            json.dump(settings, settings_file, indent=4, separators=(",", ": "))
        self.saved_settings = copy.deepcopy(self.current_settings)
        self.CheckForSettingsChange()

    def SelectOutFile(self):
        dir = QFileDialog.getExistingDirectory(self, "Directory select", os.path.expanduser("~"))
        self.current_settings["out_file"] = dir + '/report.html'
        self.ui.output_location_edit.setText(self.current_settings["out_file"])
        self.CheckForSettingsChange()
    
    def ChangeOutFilePath(self):
        path = self.ui.output_location_edit.text()
        self.current_settings["out_file"] = path
        self.CheckForSettingsChange()

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
        if "cpp" in self.current_settings["extensions"] or \
           "cc" in self.current_settings["extensions"] or \
           "c" in self.current_settings["extensions"]:
            if "c" in self.current_settings["extensions"]:
                if not "cpp" in self.current_settings["extensions"]:
                    self.current_settings["extensions"].insert(self.current_settings["extensions"].index("c"), "cpp")
                if not "cc" in self.current_settings["extensions"]:
                  self.current_settings["extensions"].insert(self.current_settings["extensions"].index("c"), "cc")
            elif "cpp" in self.current_settings["extensions"]:
                if not "c" in self.current_settings["extensions"]:
                  self.current_settings["extensions"].insert(self.current_settings["extensions"].index("cpp"), "c")
                if not "cc" in self.current_settings["extensions"]:
                  self.current_settings["extensions"].insert(self.current_settings["extensions"].index("cpp"), "cc")
            else:
                if not "c" in self.current_settings["extensions"]:
                  self.current_settings["extensions"].insert(self.current_settings["extensions"].index("cc"), "c")
                if not "cpp" in self.current_settings["extensions"]:
                  self.current_settings["extensions"].insert(self.current_settings["extensions"].index("cc"), "cpp")
        self.ui.extensions_c_source_checkbox.setChecked("c" in self.current_settings["extensions"] or "cpp" in self.current_settings["extensions"])
        if "h" in self.current_settings["extensions"] or "hpp" in self.current_settings["extensions"]:
            if "h" in self.current_settings["extensions"]:
                if not "hpp" in self.current_settings["extensions"]:
                  self.current_settings["extensions"].insert(self.current_settings["extensions"].index("h"), "hpp")
            else:
                if not "h" in self.current_settings["extensions"]:
                  self.current_settings["extensions"].insert(self.current_settings["extensions"].index("hpp"), "h")
        self.ui.extensions_c_header_checkbox.setChecked("h" in self.current_settings["extensions"] or "hpp" in self.current_settings["extensions"])
        self.ui.extensions_python_checkbox.setChecked("py" in self.current_settings["extensions"])
        other_types = []
        for ext in self.current_settings["extensions"]:
            if ext not in ["c", "cpp", "cc", "h", "hpp", "py"]:
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
        self.ui.output_location_edit.setText(self.current_settings["out_file"])
        self.ui.run_button.setEnabled(len(self.current_settings["test_directories"]) and \
                                      len(self.current_settings["reference_directories"]) and \
                                      len(self.current_settings["boilerplate_directories"]))

        self.CheckForSettingsChange()

    def CheckForSettingsChange(self):
        # set unsaved state for window title
        print(self.saved_settings)
        print(self.current_settings)
        if self.current_settings != self.saved_settings:
            if self.windowTitle()[-1] != '*':
                self.setWindowTitle(self.windowTitle() + '*')
            return True
        else:
            if self.windowTitle()[-1] == '*' and not 'Untitled' in self.windowTitle():
                self.setWindowTitle(self.windowTitle()[:-1])
            return False

    # add button connection redirection funcs
    def AddDir_test(self):
        self.AddDir("test_directories")
    def AddDir_ref(self):
        self.AddDir("reference_directories")
    def AddDir_bp(self):
        self.AddDir("boilerplate_directories")
    # main one
    def AddDir(self, type):
        initdir = os.path.expanduser("~") \
            if self.SettingsFileName == "" or not os.path.isfile(self.SettingsFileName) \
            else self.SettingsFileName
        dir = QFileDialog.getExistingDirectory(self, "Directory select", initdir)
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
        self.EditExt(["cpp", "cc", "c"], self.ui.extensions_c_source_checkbox.isChecked())
    def EditExt_h(self):
        self.EditExt(["hpp", "h"], self.ui.extensions_c_header_checkbox.isChecked())
    def EditExt_py(self):
        self.EditExt(["py"], self.ui.extensions_python_checkbox.isChecked())
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
    
    def EditThres_noise(self):
        self.EditThres("noise_threshold")
    def EditThres_guar(self):
        self.EditThres("guarantee_threshold")
    def EditThres_disp(self):
        self.EditThres("display_threshold")
    def EditThres(self, type):
        if type == "noise_threshold":
            val = self.ui.thresholds_noise_spinbox.value()
        elif type == "guarantee_threshold":
            val = self.ui.thresholds_guarantee_spinbox.value()
        else:
            val = self.ui.thresholds_display_spinbox.value()
        self.current_settings[type] = val
        self.UpdateUI()

    def EditAdd_samename(self):
        self.current_settings["same_name_only"] = self.ui.additional_samename_checkbox.isChecked()
        self.UpdateUI()
    def EditAdd_leaf(self):
        self.current_settings["ignore_leaf"] = self.ui.additional_sameleaf_checkbox.isChecked()
        self.UpdateUI()
    def EditAdd_filt(self):
        self.current_settings["disable_filtering"] = self.ui.additional_filtering_checkbox.isChecked()
        self.UpdateUI()
    def EditAdd_autoopen(self):
        self.current_settings["disable_autoopen"] = self.ui.additional_autoopen_checkbox.isChecked()
        self.UpdateUI()
    def EditAdd_truncate(self):
        self.current_settings["truncate"] = self.ui.additional_truncate_checkbox.isChecked()
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
