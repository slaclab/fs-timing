import sys
import random
from os import path
from pydm import Display
from PySide2 import QtCore, QtWidgets, QtGui
import json
import epics

class MyDisplay(Display):
    def __init__(self, parent=None, args=None, macros=None):
        super(MyDisplay, self).__init__(parent=parent, args=args, macros=macros)
        config_path = 'proto_fsmanager_config.json'
        with open(config_path,'r') as fp:
            self.config = json.load(fp)
        self.configure_controls()

    def ui_filename(self):
        return 'fsmanager_gui.ui'

    def ui_filepath(self):
        return path.join(path.dirname(path.realpath(__file__)), self.ui_filename())

    def configure_controls(self):
        self.ui.sxrpcav1val.channel = "ca://" + self.config["pvs"]["pcav3PV"]
        self.ui.sxrpcav2val.channel = "ca://" + self.config["pvs"]["pcav4PV"]
        self.ui.hxrpcav1val.channel = "ca://" + self.config["pvs"]["pcav1PV"]
        self.ui.hxrpcav2val.channel = "ca://" + self.config["pvs"]["pcav2PV"]
        # self.ui.pcavTimePlot.init_y_channels = ["ca://" + self.config["pvs"]["pcav3PV"],"ca://" + self.config["pvs"]["pcav4PV"], "ca://" + self.config["pvs"]["pcav1PV"],"ca://" + self.config["pvs"]["pcav2PV"]]
        # self.ui.cabstabTimePlot.init_y_channels = ["ca://" + self.config["pvs"]["fehphaseshifterPV"],"ca://" + self.config["pvs"]["nehphaseshifterPV"]]
        self.ui.fehfboffset_val.channel = "ca://" + self.config["pvs"]["fehFBOffset"]
        self.ui.nehfboffset_val.channel ="ca://" + self.config["pvs"]["nehFBOffset"]
        self.ui.fehfbgain_val.channel ="ca://" + self.config["pvs"]["fehFBGain"]
        self.ui.nehfbgain_val.channel ="ca://" + self.config["pvs"]["nehFBGain"]
        self.ui.fehfbenable_ctl.init_channel ="ca://" + self.config["pvs"]["fehFBEnable"]
        self.ui.fehfbenable_ctl.addItems(["Disabled","Enabled"])
        self.ui.fehfbenable_ctl.currentIndexChanged.connect(lambda: self.fbenable_toggle(self.config["pvs"]["fehFBEnable"],self.ui.fehfbenable_ctl.currentIndex()))
        self.ui.fehfbenable_ctl.setEnabled(True)
        self.ui.nehfbenable_ctl.init_channel ="ca://" + self.config["pvs"]["nehFBEnable"]
        self.ui.nehfbenable_ctl.addItems(["Disabled","Enabled"])
        self.ui.nehfbenable_ctl.currentIndexChanged.connect(lambda: self.fbenable_toggle(self.config["pvs"]["nehFBEnable"],self.ui.nehfbenable_ctl.currentIndex()))
        self.ui.nehfbenable_ctl.setEnabled(True)
        self.updateEnableState()
        self.ui.zerofehoffsets_push.channel = "ca://" + self.config["pvs"]["fehFBRequestZero"]
        self.ui.zerofehoffsets_push.pressValue = 1
        self.ui.zeronehoffsets_push.channel = "ca://" + self.config["pvs"]["nehFBRequestZero"]
        self.ui.zeronehoffsets_push.pressValue = 1
        # self.ui.help_push.connect(self.displayhelp)
        # self.hxrenable = epics.PV(self.config["pvs"]["fehFBEnable"])
        # self.sxrenable = epics.PV(self.config["pvs"]["nehFBEnable"])

    def updateEnableState(self):
        ii = epics.PV(self.config["pvs"]["fehFBEnable"]).get()
        self.ui.fehfbenable_ctl.setCurrentIndex(int(ii))
        ii = epics.PV(self.config["pvs"]["nehFBEnable"]).get()
        self.ui.nehfbenable_ctl.setCurrentIndex(int(ii))

    def fbenable_toggle(self,pv,ii):
        epics.PV(pv).put(value=ii)
        print("%s fb change to %i" %(pv,ii))
        pass

    def zeroCurrentOffsets(self,pv):
        """ Write a request to zero the pcav offsets to the controller code.
        """
        epics.PV(pv).put(value=1)
