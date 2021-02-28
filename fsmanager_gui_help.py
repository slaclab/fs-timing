import sys
from os import path
from pydm import Display
from PySide2 import QtCore, QtWidgets, QtGui
import pdb

class MyDisplay(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(MyDisplay, self).__init__(parent=parent, args=args, macros=macros)
        with open("fsmanager_gui_help.html",'r') as fp:
            self.ui.webEngineView.setHtml(fp.read())

    def ui_filename(self):
        return 'fsmanager_gui_help.ui'

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())