#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Gerasimov Alexander <samik.mechanic@gmail.com>
#

import sys, os, json, platform, webbrowser, copy, re, subprocess, pathlib

import resource
from io import StringIO
from copydetect import *
from mainform import Ui_MainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow,
    QFileDialog, QMessageBox,
    QShortcut, QAction
)
from PyQt5.QtGui import (
    QIcon, QStandardItemModel, QStandardItem,
    QKeySequence
)

# handle high resolution displays
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

def _repr_interactive(text: str):
    copy_start = 0
    _str = ""
    for i in range(1, len(text)):
        char = text[i]
        if char == '\r':
            copy_start = i+1
        elif char == '\n' or i == len(text) and i-1 != copy_start:
            _str = _str + text[copy_start:i+1].replace('#', "🁢")
            i = i+1
            copy_start = i
        else:
            pass
    return _str

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
            "display_threshold" : .33,
            "same_name_only" : False,
            "ignore_leaf" : False,
            "disable_filtering" : False,
            "disable_autoopen" : False,
            "truncate" : False,
            "out_file" : os.getcwd() + '/report.html',
        }
        self.current_settings = copy.deepcopy(self.saved_settings)
        self.LoadAppSettings()
        self.recent_configs = set()
        self.LoadConfigFile()
        self.UpdateUI()
        # set icons
        self.ui.actionOpen_configuration.setIcon(QIcon(":/icons/folder"))
        self.ui.menuOpen_Recent.setIcon(QIcon(":/icons/recent"))
        self.ui.actionSave_configuration.setIcon(QIcon(":/icons/save"))
        self.ui.actionSave_configuration_as.setIcon(QIcon(":/icons/saveas"))
        self.ui.actionHelp_Help.setIcon(QIcon(":/icons/help"))
        self.ui.actionHelp_About.setIcon(QIcon(":/icons/about"))
        self.ui.run_button.setIcon(QIcon(":/icons/run"))
        # connect menubar actions
        self.ui.actionOpen_configuration.triggered.connect(self.OpenConfigFile)
        self.ui.actionSave_configuration.triggered.connect(self.SaveConfigFile)
        self.ui.actionSave_configuration_as.triggered.connect(self.SaveConfigFileAs)
        self.ui.actionHelp_Help.triggered.connect(self.OpenHelp)
        self.ui.actionHelp_About.triggered.connect(self.About)
        # add/remove from list buttons
        self.ui.test_dirs_button_add.clicked.connect(self.AddDir_test)
        self.ui.ref_dirs_button_add.clicked.connect(self.AddDir_ref)
        self.ui.bp_dirs_button_add.clicked.connect(self.AddDir_bp)
        # global shortcut for quick deletion of directory from focused list
        QShortcut(QKeySequence("Backspace"), self, self.DelDir_fromshortcut)
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
        # run button
        self.ui.run_button.clicked.connect(self.Run)

    def _apply_workarounds(self):
        # update 'other' extensions value to settings dict
        self.EditExt_other()
        # if no extensions been selected - set all formats
        if not len(self.current_settings["extensions"]):
            self.current_settings["extensions"] = ["*"]
        # Copydetect -c run requires that reference_directories list should not be empty.
        # If it is so - get reference_directories list equal to test_directories list
        if not len(self.current_settings["reference_directories"]):
            self.current_settings["reference_directories"] = copy.deepcopy(self.current_settings["test_directories"])
            self.UpdateUI()

    def _get_app_path(self):
        appdir = str(pathlib.Path.home())
        if sys.platform == "win32":
            appdir += "/AppData/Roaming"
        elif sys.platform == "linux":
            appdir += "/.local/share"
        elif sys.platform == "darwin":
            appdir += "/Library/Application Support"
        appdir += "/CopyDetectGUI"
        try: os.makedirs(appdir)
        except FileExistsError: pass
        return appdir + "/settings.json"

    def LoadAppSettings(self):
        settings_path = self._get_app_path()
        if not os.path.isfile(settings_path):
            self.SettingsFileName = ""
            self.last_selected_dir = os.path.expanduser("~")
        else:
            app_settings = json.load(open(settings_path, "r"))
            self.SettingsFileName = app_settings["last_config_file"]
            self.last_selected_dir = app_settings["last_selected_dir"]
            # backward compatibility with v0.1
            # saving last window state was added in v0.2
            try:
                self.resize(*app_settings["window_size"])
            except KeyError:
                pass
            try:
                self.move(*app_settings["window_pos"])
            except KeyError:
                pass

    def LoadRecentConfigFile(self):
        if type(self.sender()) == QAction:
            self.SettingsFileName = self.sender().text()
            self.LoadConfigFile()
            self.UpdateUI()
        else:
            pass # illegal sender

    def LoadConfigFile(self):
        if os.path.isfile(self.SettingsFileName):
            settings = json.load(open(self.SettingsFileName, "r"))
            for key in settings.keys():
                self.current_settings[key] = settings[key]
            # refresh change state
            self.saved_settings = copy.deepcopy(self.current_settings)
            self.setWindowTitle("CopyDetect UI - " + self.SettingsFileName)
            self.recent_configs.add(self.SettingsFileName)

    def OpenConfigFile(self):
        if self.SettingsFileName != "" or os.path.isfile(self.SettingsFileName):
            self.last_selected_dir = self.SettingsFileName
        file, _ = QFileDialog.getOpenFileName(self, "Open configuration", self.last_selected_dir, "CopyDetect settings (*.json)")
        if file == "" or not os.path.isfile(file):
            return
        self.last_selected_dir = file
        self.SettingsFileName = file
        self.LoadConfigFile()
        self.UpdateUI()

    def SaveAppSettings(self):
        settings_path = self._get_app_path()
        app_settings = {
            "last_config_file": self.SettingsFileName,
            "last_selected_dir": self.last_selected_dir,
            "window_size": [ self.width(), self.height() ],
            "window_pos": [ self.pos().x(), self.pos().y() ]
        }
        json.dump(app_settings, open(settings_path, "w"), \
                  indent=2, ensure_ascii=False, separators=(",", ": "))

    def SaveConfigFile(self):
        if not self.CheckForSettingsChange():
            return False
        if self.SettingsFileName == "" or not os.path.isfile(self.SettingsFileName):
            return self.SaveConfigFileAs()
        else:
            self._apply_workarounds()
            json.dump(self.current_settings, open(self.SettingsFileName, "w"), \
                      indent=2, ensure_ascii=False, separators=(",", ": "))
            self.saved_settings = copy.deepcopy(self.current_settings)
            self.CheckForSettingsChange()
        return True

    def SaveConfigFileAs(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save new configuration", self.last_selected_dir, "CopyDetect settings (*.json)")
        if file == "":
            return False
        self.last_selected_dir = file
        self.SettingsFileName = file
        self._apply_workarounds()
        json.dump(self.current_settings, open(self.SettingsFileName, "w"), \
                  indent=2, ensure_ascii=False, separators=(",", ": "))
        self.saved_settings = copy.deepcopy(self.current_settings)
        self.setWindowTitle("CopyDetect UI - " + self.SettingsFileName)
        self.CheckForSettingsChange()
        return True

    def SelectOutFile(self):
        dir = QFileDialog.getExistingDirectory(self, "Directory select", self.last_selected_dir)
        if dir == "":
            return
        self.last_selected_dir = dir
        self.current_settings["out_file"] = dir + '/report.html'
        self.ui.output_location_edit.setText(self.current_settings["out_file"])
        self.CheckForSettingsChange()
    
    def ChangeOutFilePath(self):
        path = self.ui.output_location_edit.text()
        self.current_settings["out_file"] = path
        self.CheckForSettingsChange()

    def UpdateUI(self):
        # refill recent files menubar
        recents = []
        for action in self.ui.menuOpen_Recent.actions():
            self.ui.menuOpen_Recent.removeAction(action)
        for file in self.recent_configs:
            baritem = QAction(file, self.ui.menuOpen_Recent)
            baritem.setIcon(QIcon(":/icons/file"))
            baritem.setEnabled(file != self.SettingsFileName)
            baritem.triggered.connect(self.LoadRecentConfigFile)
            recents.append(baritem)
        self.ui.menuOpen_Recent.addActions(recents)
        # fill directory lists
        model = QStandardItemModel(self.ui.test_dirs_list)
        for dir in self.current_settings["test_directories"]:
            item = QStandardItem(QIcon(":/icons/folder"), dir)
            item.setEditable(False)
            model.appendRow(item)
        self.ui.test_dirs_list.setModel(model)
        model = QStandardItemModel(self.ui.test_dirs_list)
        for dir in self.current_settings["reference_directories"]:
            item = QStandardItem(QIcon(":/icons/folder"), dir)
            item.setEditable(False)
            model.appendRow(item)
        self.ui.ref_dirs_list.setModel(model)
        model = QStandardItemModel(self.ui.test_dirs_list)
        for dir in self.current_settings["boilerplate_directories"]:
            item = QStandardItem(QIcon(":/icons/folder"), dir)
            item.setEditable(False)
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
            if ext not in ["c", "cpp", "cc", "h", "hpp", "py", "*"]:
                other_types.append(ext)
        if len(other_types):
            self.ui.extensions_other_checkbox.setChecked(True)
            self.ui.extensions_other_edit.setText(",  ".join(ex for ex in other_types))
            self.ui.extensions_other_edit.setEnabled(True)
        self.ui.thresholds_noise_spinbox.setValue(self.current_settings["noise_threshold"])
        self.ui.thresholds_guarantee_spinbox.setValue(self.current_settings["guarantee_threshold"])
        self.ui.thresholds_display_spinbox.setValue(int(self.current_settings["display_threshold"]*100))
        self.ui.additional_samename_checkbox.setChecked(self.current_settings["same_name_only"])
        self.ui.additional_sameleaf_checkbox.setChecked(self.current_settings["ignore_leaf"])
        self.ui.additional_filtering_checkbox.setChecked(self.current_settings["disable_filtering"])
        self.ui.additional_autoopen_checkbox.setChecked(self.current_settings["disable_autoopen"])
        self.ui.additional_truncate_checkbox.setChecked(self.current_settings["truncate"])
        self.ui.output_location_edit.setText(self.current_settings["out_file"])
        self.ui.run_button.setEnabled(len(self.current_settings["test_directories"]))

        self.CheckForSettingsChange()

    def CheckForSettingsChange(self):
        # set unsaved state for window title
        # print(self.saved_settings)
        # print(self.current_settings)
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
        dir = QFileDialog.getExistingDirectory(self, "Directory select", self.last_selected_dir)
        if dir == "":
            return
        self.last_selected_dir = dir
        if dir not in self.current_settings[type]:
            self.current_settings[type].append(dir)
        self.UpdateUI()

    # remove button connection from global window shortcut 
    def DelDir_fromshortcut(self):
        focused = self.focusWidget()
        print(focused)
        print(self.ui.test_dirs_list)
        if focused == self.ui.test_dirs_list:
            self.DelDir_test()
        elif focused == self.ui.ref_dirs_list:
            self.DelDir_ref()
        elif focused == self.ui.bp_dirs_list:
            self.DelDir_bp()
        else:
            pass
    # remove button connection redirection funcs
    def DelDir_test(self):
        self.DelDir("test_directories")
    def DelDir_ref(self):
        self.DelDir("reference_directories")
    def DelDir_bp(self):
        self.DelDir("boilerplate_directories")
    # main one
    def DelDir(self, type):
        idx = None
        if type == "test_directories":
            idx = self.ui.test_dirs_list.currentIndex()
            to_del = idx.data(Qt.DisplayRole)
        elif type == "reference_directories":
            idx = self.ui.ref_dirs_list.currentIndex()
            to_del = idx.data(Qt.DisplayRole)
        else: # bp dir
            idx = self.ui.bp_dirs_list.currentIndex()
            to_del = idx.data(Qt.DisplayRole)
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
        self.EditExt(exts, enable)
    def EditExt(self, exts, enable=True):
        if "*" in self.current_settings["extensions"]:
            self.current_settings["extensions"].remove("*")
        for ext in exts:
            if enable:
                if ext not in self.current_settings["extensions"]:
                    self.current_settings["extensions"].append(ext)
            else:
                if ext in self.current_settings["extensions"]:
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
            val = float(self.ui.thresholds_display_spinbox.value())/100
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

    def Run(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            self._apply_workarounds()
            self.setEnabled(False)
            detector = CopyDetector(config=self.current_settings)
            # redirect print from stdout to variable
            stdout, stderr = sys.stdout, sys.stderr
            sys.stdout = StringIO()
            # progress bars prompt to stderr, so combine
            sys.stderr = sys.stdout
            detector.run()
            detector.generate_html_report()
            output = sys.stdout.getvalue()
            # restore stdout
            sys.stdout, sys.stderr = stdout, stderr
            # process carriage return characters due to interactive nature of CopyDetect output
            output = _repr_interactive(output)
            mbox = QMessageBox(self)
            mbox.setIcon(QMessageBox.Information)
            mbox.setWindowTitle("Done!")
            mbox.setText("Analysis finished.")
            mbox.setInformativeText("Details are shown below:")
            mbox.setDetailedText(output)
            mbox.setStandardButtons(QMessageBox.Open | QMessageBox.Ok)
            mbox.setDefaultButton(QMessageBox.Ok)
            QApplication.restoreOverrideCursor()
            if mbox.exec() == QMessageBox.Open:
                # open report folder
                try: 
                    path = os.path.normpath(os.path.dirname(self.current_settings["out_file"]))
                    if platform.system() in ['Darwin', 'Linux']:
                        subprocess.check_call(['open', '--', path])
                    else:
                        subprocess.check_call(['explorer', path])
                except:
                    pass
        except Exception as e:
            QApplication.restoreOverrideCursor()
            errbox = QMessageBox(self)
            errbox.setIcon(QMessageBox.Critical)
            errbox.setWindowTitle("Error")
            errbox.setText("Error occured during analysis:")
            errbox.setInformativeText(str(e))
            errbox.exec()
        finally:
            self.setEnabled(True)

    def closeEvent(self, event):
        # save settings
        if self.CheckForSettingsChange():
            ret = QMessageBox.question(self, "Save changes", "Save configuration changes before exit?", \
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, defaultButton=QMessageBox.Yes)
            if ret == QMessageBox.Cancel:
                event.ignore()
                return
            if ret == QMessageBox.Yes:
                if not self.SaveConfigFile():
                    event.ignore()
                    return
        self.SaveAppSettings()
        event.accept()

    def OpenHelp(self):
        if platform.system() == 'Darwin':
            client = webbrowser.get('safari')
            client.open_new_tab("https://github.com/alexmechanic/CopyDetectorGUI/blob/master/README.md")
        else:
            webbrowser.open_new_tab("https://github.com/alexmechanic/CopyDetectorGUI/blob/master/README.md")

    def About(self):
        QMessageBox.information(self, "CopyDetect UI app", \
            "Graphical interface for CopyDetect CLI\n\nTool author:\nBryson Lingenfelter @ Nevada Cyber Club\n<blingenfelter@nevada.unr.edu>\n\nGUI author:\nAlexander Gerasimov @ MIPT \n<samik.mechanic@gmail.com>")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/icons/run"))
    ex = Editor()
    ex.show()
    ex.raise_()
    sys.exit(app.exec())
