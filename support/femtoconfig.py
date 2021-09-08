import os
import pathlib
import json
import re
from epics import PV as Pv

class Config(object):
    """The base config class encapsulates the logic for reading and validating
    a configuration file. It is written around the configuration design
    described in 'femto_config.json description.md' and 'template_femto_config.json'."""
    def __init__(self):
        self.config = {}
        self.version = ""
        self.name = ""
        self.pvlist = {}
        pass

    def readConfig(self,filename):
        """Reads in a configuration file. Returns a python dictionary. Written for
        potential future overload."""
        # Validate path
        if not os.path.exists(filename):
            print("Configuration filename: %s does not exist."%(filename))
            raise ValueError
        # Determine file type
        ftype = os.path.splitext(filename)
        if ftype[1]==".json":
            self.readJsonConfig(filename)
            return

    def readJsonConfig(self,filename):
        """Reads in a json configuration file. Returns a python dictionary.
        Written to go with 'template_femto_config.json'."""
        with open(filename) as fp:
            self.config = json.load(fp)

    def validateConfig(self):
        """Parent configuration function, calls separate validation stages."""
        if self.validateConfigSyntax():
            self.validateCorePVs()
            self.validateExtraConfig()


    def validateConfigSyntax(self):
        """Performs a simple validation of the configuration file syntax. Looks
        for missing sections, invalid formatting, invalid characters."""
        return True

    def validateCorePVs(self):
        """Validates the configuration stored in the object. Note, this includes
        validating all of the PVs. In other words, this will fail if you don't
        have a running IOC instance yet."""
        err = False
        # Iterate through the config PVs, testing whether each generates a valid
        # connection point. Also expand and test the prefixed pattern PVs.
        expandedConfig = self.expandPVs(self.config)
        for pvstring in self.config['config']:
            pvtestset = []
            pvtestset.append(self.config["base"])
            with Pv(pvstring) as testpv:
                if not testpv.connect(timeout=0.5):
                    print("Connection failed: %s"%(pvstring))
                    err = True
        if err:
            # add a configuration value in the meta data that is not stored in
            # the file
            self.config["config_meta"]["config_valid"] = False
            print("Configuration invalid, fix configuration file") 
        else:
            self.config["config_meta"]["config_valid"] = True

    def printAllPVs(self):
        """Utility function that outputs a list of all defined and derived PVs
        generated from the configuration."""
        pvvals = []
        pass

    def expandPVs(self):
        """Utility function that generates an expanded PV list from a 
        configuration. It will not generate pv expansions for pvs that are
        defined but not enabled in the configuration. As such, this function
        includes program logic as part of its function."""
        pvvals = []
        pvvals.append(("freq_counter",self.config["config"]["freq_counter"]))
        pvvals.append(("phase_motor",self.config["config"]["phase_motor"]))
        #pvvals.append(("error_pv_name",self.config["config"]["error_pv_name"]))
        #pvvals.append(("version_pv_name",self.config["config"]["version_pv_name"]))
        pvvals.append(("laser_trigger",self.config["config"]["laser_trigger"]))
        pvvals.append(("watchdog",self.config["config"]["dev_base"]+"FS_WATCHDOG"))
        pvvals.append(("oscillator_f",self.config["config"]["dev_base"]+"FS_OSC_TGT_FREQ"))
        pvvals.append(("time",self.config["config"]["dev_base"]+"FS_TGT_TIME"))
        pvvals.append(("time_hihi",self.config["config"]["dev_base"]+"FS_TGT_TIME.HIHI"))
        pvvals.append(("time_lolo",self.config["config"]["dev_base"]+"FS_TGT_TIME.LOLO"))
        pvvals.append(("calibrate",self.config["config"]["dev_base"]+"FS_START_CALIB"))
        pvvals.append(("enable",self.config["config"]["dev_base"]+"FS_ENABLE_TIME_CTRL"))
        pvvals.append(("busy",self.config["config"]["dev_base"]+"FS_CTRL_BUSY"))
        pvvals.append(("bucket_counter",self.config["config"]["dev_base"]+"FS_CORRECTION_CNT"))
        pvvals.append(("bucket_error",self.config["config"]["dev_base"]+"FS_BUCKET_ERROR"))
        pvvals.append(("calib_error",self.config["config"]["dev_base"]+"FS_CALIB_ERROR"))
        pvvals.append(("deg_Sband",self.config["config"]["dev_base"]+"PDES"))
        pvvals.append(("deg_offset",self.config["config"]["dev_base"]+"POC"))
        pvvals.append(("delay",self.config["config"]["dev_base"]+"FS_TRIGGER_DELAY"))
        pvvals.append(("enable_trig",self.config["config"]["dev_base"]+"FS_ENABLE_TRIGGER"))
        pvvals.append(("error",self.config["config"]["dev_base"]+"FS_TIMING_ERROR"))
        pvvals.append(("fix_bucket",self.config["config"]["dev_base"]+"FS_ENABLE_BUCKET_FIX"))
        pvvals.append(("ns_offset",self.config["config"]["dev_base"]+"FS_NS_OFFSET"))
        pvvals.append(("offset",self.config["config"]["dev_base"]+"FS_TIMING_OFFSET"))
        pvvals.append(("ok",self.config["config"]["dev_base"]+"FS_LASER_OK"))
        #pvvals.append(("time_hihi",self.config["config"]["dev_base"]+"FS_TGT_TIME.HIHI"))
        pvvals.append(("counter_jitter",self.config["config"]["dev_base"]+"GetMeasJitter"))
        pvvals.append(("counter_jitter_high",self.config["config"]["dev_base"]+"GetMeasJitter.HIGH"))
        #pvvals.append(("freq_counter",self.config["config"]["dev_base"]+""))
        #pvvals.append(("",self.config["config"]["dev_base"]+""))
        pvvals.append(("phase_motor_rb",self.config["config"]["phase_motor"]+".RBV"))
        pvvals.append(("freq_sp",self.config["config"]["dev_base"]+"FREQ_SP"))
        pvvals.append(("freq_err",self.config["config"]["dev_base"]+"FREQ_ERR"))
        pvvals.append(("rf_pwr",self.config["config"]["dev_base"]+"CH1_RF_PWR"))
        pvvals.append(("rf_pwr_lolo",self.config["config"]["dev_base"]+"CH1_RF_PWR.LOLO"))
        pvvals.append(("rf_pwr_hihi",self.config["config"]["dev_base"]+"CH1_RF_PWR.HIHI"))
        pvvals.append(("diode_pwr",self.config["config"]["dev_base"]+"CH1_DIODE_PWR"))
        pvvals.append(("diode_pwr_lolo",self.config["config"]["dev_base"]+"CH1_DIODE_PWR.LOLO"))
        pvvals.append(("diode_pwr_hihi",self.config["config"]["dev_base"]+"CH1_DIODE_PWR.HIHI"))
        #pvvals.append(("laser_trigger",self.config["config"]["dev_base"]+""))
        pvvals.append(("laser_locked",self.config["config"]["dev_base"]+"PHASE_LOCKED"))
        pvvals.append(("lock_enable",self.config["config"]["dev_base"]+"RF_LOCK_ENABLE"))
        pvvals.append(("unfixed_error",self.config["config"]["dev_base"]+"FS_UNFIXED_ERROR"))

        self.name = self.config["config"]["name"]
        self.use_secondary_calibration = self.config["config"]["use_secondary_calibration"]
        if self.use_secondary_calibration:
            pvvals.append(("secondary_calibration_enable",self.config["config"]["matlab_pv_base"]+"01"))
            pvvals.append(("secondary_calibration",self.config["add_config"]["secondary_calibration"]))
            pvvals.append(("secondary_calibration_s",self.config["config"]["matlab_pv_base"]+"02"))
            pvvals.append(("secondary_calibration_c",self.config["config"]["matlab_pv_base"]+"03"))

        self.use_drift_correction = self.config["config"]["use_drift_correction"]
        if self.use_drift_correction:
            pvvals.append(("drift_correction_signal",self.config["config"]["matlab_pv_base"]+"29"))
            pvvals.append(("drift_correction_value",self.config["config"]["matlab_pv_base"]+"04"))
            pvvals.append(("drift_correction_offset",self.config["config"]["matlab_pv_base"]+"05"))
            pvvals.append(("drift_correction_gain",self.config["config"]["matlab_pv_base"]+"06"))
            pvvals.append(("drift_correction_smoothing",self.config["config"]["matlab_pv_base"]+"07"))
            pvvals.append(("drift_correction_accum",self.config["config"]["matlab_pv_base"]+"09"))
            self.drift_correction_multiplier = -1/(2.856 * 360)

        self.use_dither = self.config["config"]["use_dither"]
        if self.use_dither:
            pvvals.append(("dither_level",self.config["add_config"]["dither_level"]))

        self.reverse_counter = self.config["config"]["reverse_counter"]
        if self.reverse_counter:
            pvvals.append(("counter",self.config["config"]["counter_base"]+"GetOffsetInvMeasMean"))
            pvvals.append(("counter_low",self.config["config"]["counter_base"]+"GetOffsetInvMeasMean.LOW"))
            pvvals.append(("counter_high",self.config["config"]["counter_base"]+"GetOffsetInvMeasMean.HIGH"))
        else:
            pvvals.append(("counter",self.config["config"]["counter_base"]+"GetMeasMean"))
            pvvals.append(("counter_low",self.config["config"]["counter_base"]+"GetMeasMean.LOW"))
            pvvals.append(("counter_high",self.config["config"]["counter_base"]+"GetMeasMean.HIGH"))

        self.is_atca = 0
        if self.config["config"]["type"] == "ATCA":
            self.is_atca = 1
            pvvals.append(('lock_enable',self.config["add_config"]["atca_base"]+'RF_LOCK_ENABLE'))
            pvvals.append(('laser_locked',self.config["add_config"]["atca_base"]+'PHASE_LOCKED'))
            pvvals.append(('rf_pwr',self.config["add_config"]["atca_base"]+'RF_PWR'))
            pvvals.append(('rf_pwr_lolo',self.config["add_config"]["atca_base"]+'RF_PWR.LOLO'))
            pvvals.append(('rf_pwr_hihi',self.config["add_config"]["atca_base"]+'RF_PWR.HIHI'))
            pvvals.append(('diode_pwr',self.config["add_config"]["atca_base"]+'DIODE_PWR'))
            pvvals.append(('diode_pwr_lolo',self.config["add_config"]["atca_base"]+'DIODE_PWR.LOLO'))
            pvvals.append(('diode_pwr_hihi',self.config["add_config"]["atca_base"]+'DIODE_PWR.HIHI'))
        
        # self.error_pv = self.config["config"]["dev_base"]+"FS_STATUS"
        # self.error_pv = self.config["config"]["error_pv_name"]
        # pvvals.append(("error_pv",self.error_pv))
        # pvvals.append(("error_pv_name",self.config["config"]["dev_base"]+"FS_STATUS"))
        self.matlab_pv_digits = self.config["config"]["matlab_pv_digits"]
        self.reverse_counter = self.config["config"]["reverse_counter"]
        self.timeout = self.config["config"]["timeout"]
        self.trig_in_ticks = self.config["config"]["trig_in_ticks"]
        self.use_combined_counter = self.config["config"]["use_combined_counter"]
        self.use_dither = self.config["config"]["use_dither"]
        self.use_drift_correction = self.config["config"]["use_drift_correction"]
        self.version_pv_name = self.config["config"]["version_pv_name"]
        self.version_pv = Pv(self.config["config"]["version_pv_name"])
        self.error_pv = Pv(self.config["config"]["error_pv_name"])
        # pvvals.append(("version_pv",self.version_pv_name))
        pvvals.append(("phase_motor_dmov",self.config["config"]["phase_motor"]+".DMOV"))

        # self.pvlist = pvvals
        for entry in pvvals:
            self.pvlist[entry[0]]=Pv(entry[1])
        # print(self.pvlist)     

    def printDefs(self):
        """Utility function that outputs a list of all functional
        definitions. These do not include PVs. This is based on scanning, not
        what is defined in code."""
        boolvals = "Boolean Values\n"
        floatvals = "Float Values\n"
        intvals = "Integer Values\n"
        stringvals = "String Values\n"
        # Iterate through the entries in the configurations, matching them
        # against each type of argument. Do this for both the config and
        # additional config
        for entry in iter(self.config["config"].items()):
            if type(entry[1])==bool:
                boolvals = boolvals + "%s:\t%s\n"%(entry[0],entry[1])
            elif type(entry[1])==float:
                floatvals = floatvals + "%s:\t%s\n"%(entry[0],entry[1])
            elif type(entry[1])==int:
                intvals = intvals + "%s:\t%s\n"%(entry[0],entry[1])
            elif type(entry[1])==str:
                if not re.match("([a-zA-Z0-9]+):",entry[1]):
                    stringvals = stringvals + "%s:\t%s\n"%(entry[0],entry[1])
        boolvals = boolvals + "- add config\n"
        floatvals = floatvals + "- add config\n"
        intvals = intvals + "- add config\n"
        stringvals = stringvals + "- add config\n"
        for entry in iter(self.config["add_config"].items()):
            if type(entry[1])==bool:
                boolvals = boolvals + "%s:\t%s\n"%(entry[0],entry[1])
            elif type(entry[1])==float:
                floatvals = floatvals + "%s:\t%s\n"%(entry[0],entry[1])
            elif type(entry[1])==int:
                intvals = intvals + "%s:\t%s\n"%(entry[0],entry[1])
            elif type(entry[1])==str:
                if not re.match("([a-zA-Z0-9]+):",entry[1]):
                    stringvals = stringvals + "%s:\t%s\n"%(entry[0],entry[1])
        # Print out the built strings that represent everything that isn't a PV
        print(boolvals)
        print(floatvals)
        print(intvals)
        print(stringvals)

    def validateExtraConfig(self):
        """Performs a validation on the additional parameters provided in the
        configuration file. Will not result in a validation failure, but will
        indicate if parameters are not accessible."""
        pass

    def generateConfig(path,self):
        """This utility function will generate an empty configuration file."""
        # Not yet implemented
        pass

    