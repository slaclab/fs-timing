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
            print("Configuration filename does not exist.")
            return
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
        pvvals.append(("error_pv_name",self.config["config"]["error_pv_name"]))
        pvvals.append(("version_pv_name",self.config["config"]["version_pv_name"]))
        pvvals.append(("laser_trigger",self.config["config"]["laser_trigger"]))
        pvvals.append(("watchdog",self.config["config"]["dev_base"]+"FS_WATCHDOG"))
        pvvals.append(("oscillator_f",self.config["config"]["dev_base"]+"FS_OSC_TGT_FREQ"))
        pvvals.append(("time",self.config["config"]["dev_base"]+"FS_TGT_TIME"))
        pvvals.append(("time_hihi",self.config["config"]["dev_base"]+"FS_TGT_TIME_HIHI"))
        pvvals.append(("time_lolo",self.config["config"]["dev_base"]+"FS_TGT_TIME.LOLO"))
        pvvals.append(("calibrate",self.config["config"]["dev_base"]+"FS_START_CALIB"))
        pvvals.append(("enable",self.config["config"]["dev_base"]+"FS_ENABLE_TIME_CTRL"))
        pvvals.append(("busy",self.config["config"]["dev_base"]+"FS_CTRL_BUSY"))

        if self.config["config"]["use_drift_correction"]:
            pvvals.append(())

        self.name = self.config["config"]["name"]
        self.use_secondary_calibration = self.config["config"]["use_secondary_calibration"]
        if self.config["config"]["type"] == "ATCA":
            self.is_atca = 1
        self.error_pv_name = self.config["config"]["dev_base"]+"FS_STATUS"

        # self.pvlist = pvvals
        for entry in pvvals:
            self.pvlist[entry[0]]=Pv(entry[1])
        # print(self.pvlist)

    def expandV1defsInParent(self):
        """As part of incremental refactoring of femto.py, this function will
        expand the imported configuration to an array of dictionaries which is then
        dehydrated in femto.py to match that of what is used in the base v1.x
        femto.py. The intent is that this will become deprecated upon refactor
        of femto.py to further remove legacy hard-coded structures, but is
        necessary in the short term for testing femto.py with configurations
        removed from the parent code."""
        #exarray = 
        self.version = 'Watchdog 141126a' # version string; not sure what this originally was, but see no reason not to re-use
        self.name = self.config["config"]["name"]
        print(self.name)
        namelist = set()
        self.pvlist = dict()  # will hold pvs with names
        matlab_list = dict() # list of matlab style pvs, tuples of matlab number offset and pv description
        matlab_pv_base = dict() # header matlab pvs like SIOC:SYS0:ML00:OA....
        matlab_pv_offset = dict() # start number for pvs
        matlab_pv_digits = dict()  # number of digits for each pv
        matlab_use = dict() # set to true if this matlab pv shoudl be used even if a ioc pv exists defined below.
        for n in range(0,20):
            matlab_use[n] = True  # initize to always use matlab, override to use epics pvs.
        counter_base = dict()  # holds counter name
        freq_counter = dict() # frequencycounter name
        dev_base = dict() # used to generate other device names (mostl future)
        atca_base = dict() # used for ATCA PV names
        phase_motor = dict()
        laser_trigger = dict()
        trig_in_ticks = dict() # 1 if trigger units are ticks (1/119MHz), 0 if in nanoseconds( kludge for multi systems)
        reverse_counter = dict()  # 1 if the laser starts the counter, trigger stops.        
        error_pv_name = dict()    
        use_secondary_calibration = dict() # use a scope or other device
        is_atca = dict() # holds whether the system is an ATCA system
        for n in range(0,20):
            use_secondary_calibration[n] = False  # Turn off except where needed.
        secondary_calibration_enable = dict() # set to 1 to enable secondary calibration
        secondary_calibration = dict() # the pv to use for secondary calibration
        secondary_calibration_s = dict() # sine term for calibration
        secondary_calibration_c = dict() # cosine term for calibration
        use_drift_correction = dict() # used to set up the drifty correction based on LBNL
        drift_correction_signal = dict() # what PV to read
        drift_correction_multiplier = dict() # multiples the signal to get value
        drift_correction_value = dict() # PV the current reading in ns.
        drift_correction_offset = dict() # PV in final nanoseconds
        drift_correction_gain = dict()  # PV nanoseconds / pv value, 0 is disable
        drift_correction_smoothing = dict()  # number of pulse to exponential average
        drift_correction_accum = dict() # enables/disables drift correction accumulation (I term)
        for n in range(0,20):
            use_drift_correction[n] = False  # Turn off except where needed.
        use_dither = dict() # used to allow fast dither of timing (for special functions)
        dither_level = dict()  # amount of dither in picoseconds
        for n in range(0,20):
            use_dither[n] = False  # Turn off except where needed.
        version_pv_name = dict()
        matlab = dict()  # holds all matlab use pvs
        timeout = 1.0  # default timeout for connecting to pvs

        nm = 'CXI'
        namelist.add(nm)
        base = 'LAS:FS5:'  # base name for this sysetm
        dev_base[nm] = base+'VIT:'
        matlab_pv_base[nm] = dev_base[nm]+'matlab:'
        matlab_pv_offset[nm] = 1
        matlab_pv_digits[nm] = 2
        counter_base[nm] = base+'CNT:TI:'   # time interval counter
        freq_counter[nm] = dev_base[nm]+'FREQ_CUR'        
        phase_motor[nm] = base+'MMS:PH' 
        error_pv_name[nm] = dev_base[nm]+'FS_STATUS' 
        version_pv_name[nm] = dev_base[nm]+'FS_WATCHDOG.DESC' 
        laser_trigger[nm] = 'LAS:R52B:EVR:31:TRIG0:TDES' # was 'LAS:SR63:EVR:09:CTRL.DG0D'
        trig_in_ticks[nm] = 0  # eEdu Granados <edu.granados@gmail.com>xperiment side triggers operate in ticks units
        reverse_counter[nm] = 1
        use_secondary_calibration[nm] = 0
        matlab_use = dict()
        for n in range(0,20):
            matlab_use[n] = False  # Use new PVs
        matlab[nm] = matlab_use    
        # modified for timetool drift draft
        drift_correction_signal[nm] = 'LAS:FS5:VIT:matlab:29' # what PV to read
        drift_correction_multiplier[nm] = -1/(2.856 * 360); 
        drift_correction_value[nm]= 'LAS:FS5:VIT:matlab:04'# PV the current reading in ns.
        drift_correction_offset[nm]= 'LAS:FS5:VIT:matlab:05' # PV in final nanoseconds
        drift_correction_gain[nm]= 'LAS:FS5:VIT:matlab:06'  # PV nanoseconds / pv value, 0 is disable
        drift_correction_smoothing[nm]='LAS:FS5:VIT:matlab:07'
        drift_correction_accum[nm]='LAS:FS5:VIT:matlab:09'
        use_drift_correction[nm] = True  
        use_dither[nm] = False # used to allow fast dither of timing (for special functions)
        
        while not (self.name in namelist):
            print(self.name + ' not found, please enter one of the following ')
            for x in namelist:
                print(x)
            self.name = raw_input('enter system name:')                           

        matlab_use = matlab[self.name]
        self.use_secondary_calibration = use_secondary_calibration[self.name]
        self.is_atca = is_atca[self.name]
        self.use_drift_correction = use_drift_correction[self.name]
        if self.use_drift_correction:
            self.drift_correction_multiplier = drift_correction_multiplier[self.name]
        self.use_dither = use_dither[self.name] # used to allow fast dither of timing (for special functions)
        if self.use_dither:
            self.dither_level = dither_level[self.name]      
        self.trig_in_ticks = trig_in_ticks[self.name]
        self.reverse_counter = reverse_counter[self.name]                     
        #matlab list holds tuples of the matlab variable index offset and description field                       
        matlab_list['watchdog'] = 0,'femto watchdog' + self.version # matlab variable and text string
        matlab_list['oscillator_f'] = 1,'femto oscillator target F' # frequency to enter in oscillator field
        matlab_list['time'] = 2,'femto target time ns' # when control is enabled, laser will move to this time on counter
        matlab_list['calibrate'] = 3,'femto enter 1 to calibrate' # used to run calibration routine
        matlab_list['enable'] = 4,'femto enable time control' # automated time control
        matlab_list['busy'] = 5,'femto control busy'
        matlab_list['error'] = 6,'timing error vs freq counter'
        matlab_list['ok'] = 7,'femto Laser OK'
        matlab_list['fix_bucket'] = 8, 'fix bucket jump' # used to fix a bucket error
        matlab_list['delay'] = 9, 'trigger delay - do not change'
        matlab_list['offset'] = 10, 'timing  offset do not change'
        matlab_list['enable_trig'] = 11, 'enable trigger control'
        matlab_list['bucket_error'] = 12, ' buckets of 3808MHz error'        
        matlab_list['unfixed_error'] = 13, 'error from integer buckets ns'
        matlab_list['bucket_counter'] = 14, 'bucket corrects since reset'
        matlab_list['deg_Sband'] = 15, 'Degrees S band control'
        matlab_list['deg_offset'] = 16, 'Degrees offset'
        matlab_list['ns_offset'] =  17, 'ns, offset degS control'       
        matlab_list['calib_error'] = 19, 'last calibration error ns'
        
        # List of other PVs used.
        self.pvlist['watchdog'] =  Pv(dev_base[self.name]+'FS_WATCHDOG')
        self.pvlist['oscillator_f'] =  Pv(dev_base[self.name]+'FS_OSC_TGT_FREQ')
        self.pvlist['time'] =  Pv(dev_base[self.name]+'FS_TGT_TIME')
        self.pvlist['time_hihi'] =  Pv(dev_base[self.name]+'FS_TGT_TIME.HIHI')
        self.pvlist['time_lolo'] =  Pv(dev_base[self.name]+'FS_TGT_TIME.LOLO')
        self.pvlist['calibrate'] =  Pv(dev_base[self.name]+'FS_START_CALIB')
        self.pvlist['enable'] =  Pv(dev_base[self.name]+'FS_ENABLE_TIME_CTRL')
        self.pvlist['busy'] =  Pv(dev_base[self.name]+'FS_CTRL_BUSY')
        self.pvlist['error'] =  Pv(dev_base[self.name]+'FS_TIMING_ERROR')
        self.pvlist['ok'] =  Pv(dev_base[self.name]+'FS_LASER_OK')
        self.pvlist['fix_bucket'] =  Pv(dev_base[self.name]+'FS_ENABLE_BUCKET_FIX')   
        self.pvlist['delay'] =  Pv(dev_base[self.name]+'FS_TRIGGER_DELAY')
        self.pvlist['offset'] =  Pv(dev_base[self.name]+'FS_TIMING_OFFSET')
        self.pvlist['enable_trig'] =  Pv(dev_base[self.name]+'FS_ENABLE_TRIGGER')
        self.pvlist['bucket_error'] =  Pv(dev_base[self.name]+'FS_BUCKET_ERROR')
        self.pvlist['bucket_counter'] =  Pv(dev_base[self.name]+'FS_CORRECTION_CNT')
        self.pvlist['deg_Sband'] =  Pv(dev_base[self.name]+'PDES')
        self.pvlist['deg_offset'] =  Pv(dev_base[self.name]+'POC')
        self.pvlist['ns_offset'] =  Pv(dev_base[self.name]+'FS_NS_OFFSET')
        self.pvlist['calib_error'] =  Pv(dev_base[self.name]+'FS_CALIB_ERROR')
        
        if self.reverse_counter:
            self.pvlist['counter'] = Pv(counter_base[self.name]+'GetOffsetInvMeasMean')  #time interval counter result, create Pv
            self.pvlist['counter_low'] = Pv(counter_base[self.name]+'GetOffsetInvMeasMean.LOW')        
            self.pvlist['counter_high'] = Pv(counter_base[self.name]+'GetOffsetInvMeasMean.HIGH') 
        
        else:
            self.pvlist['counter'] = Pv(counter_base[self.name]+'GetMeasMean')  #time interval counter result, create Pv
            self.pvlist['counter_low'] = Pv(counter_base[self.name]+'GetMeasMean.LOW')        
            self.pvlist['counter_high'] = Pv(counter_base[self.name]+'GetMeasMean.HIGH') 
        
        self.pvlist['counter_jitter'] = Pv(counter_base[self.name]+'GetMeasJitter')
        self.pvlist['counter_jitter_high'] = Pv(counter_base[self.name]+'GetMeasJitter.HIGH')        
        self.pvlist['freq_counter'] = Pv(freq_counter[self.name])  # frequency counter readback        
        self.pvlist['phase_motor'] = Pv(phase_motor[self.name])  # phase control smart motor
        self.pvlist['phase_motor_rb'] = Pv(phase_motor[self.name]+'.RBV')  # motor readback
        self.pvlist['freq_sp'] =  Pv(dev_base[self.name]+'FREQ_SP')  # frequency counter setpoing
        self.pvlist['freq_err'] = Pv(dev_base[self.name]+'FREQ_ERR') # frequency counter error
        self.pvlist['rf_pwr']= Pv(dev_base[self.name]+'CH1_RF_PWR') # RF power readback
        self.pvlist['rf_pwr_lolo']= Pv(dev_base[self.name]+'CH1_RF_PWR'+'.LOLO') # RF power readback
        self.pvlist['rf_pwr_hihi']= Pv(dev_base[self.name]+'CH1_RF_PWR'+'.HIHI') # RF power readback 
        self.pvlist['diode_pwr'] = Pv(dev_base[self.name]+'CH1_DIODE_PWR')
        self.pvlist['diode_pwr_lolo'] = Pv(dev_base[self.name]+'CH1_DIODE_PWR'+'.LOLO')
        self.pvlist['diode_pwr_hihi'] = Pv(dev_base[self.name]+'CH1_DIODE_PWR'+'.HIHI')
        self.pvlist['laser_trigger'] = Pv(laser_trigger[self.name])
        self.pvlist['laser_locked'] = Pv(dev_base[self.name]+'PHASE_LOCKED')
        self.pvlist['lock_enable'] = Pv(dev_base[self.name]+'RF_LOCK_ENABLE')
        self.pvlist['unfixed_error'] =  Pv(dev_base[self.name]+'FS_UNFIXED_ERROR')
  
        if self.use_secondary_calibration:
            self.pvlist['secondary_calibration'] = Pv(secondary_calibration[self.name])
            self.pvlist['secondary_calibration_enable'] = Pv(secondary_calibration_enable[self.name])
            self.pvlist['secondary_calibration_s'] = Pv(secondary_calibration_s[self.name])
            self.pvlist['secondary_calibration_c'] = Pv(secondary_calibration_c[self.name])
        if self.use_drift_correction:
            self.pvlist['drift_correction_signal'] = Pv(drift_correction_signal[self.name])
            self.pvlist['drift_correction_value'] = Pv(drift_correction_value[self.name])
            self.pvlist['drift_correction_offset'] = Pv(drift_correction_offset[self.name])
            self.pvlist['drift_correction_gain'] =  Pv(drift_correction_gain[self.name])
            self.pvlist['drift_correction_smoothing'] =  Pv(drift_correction_smoothing[self.name])
            self.pvlist['drift_correction_accum'] = Pv(drift_correction_accum[self.name])
        if self.use_dither:
            self.pvlist['dither_level'] = Pv(dither_level[self.name])
        # ASTA ATCA system replaces certain PVs
        if self.is_atca:
            self.pvlist['lock_enable'] = Pv(atca_base[self.name]+'RF_LOCK_ENABLE')
            self.pvlist['laser_locked'] = Pv(atca_base[self.name]+'PHASE_LOCKED')
            self.pvlist['rf_pwr']= Pv(atca_base[self.name]+'RF_PWR') # RF power readback
            self.pvlist['rf_pwr_lolo']= Pv(atca_base[self.name]+'RF_PWR'+'.LOLO') # RF power readback
            self.pvlist['rf_pwr_hihi']= Pv(atca_base[self.name]+'RF_PWR'+'.HIHI') # RF power readback 
            self.pvlist['diode_pwr'] = Pv(atca_base[self.name]+'DIODE_PWR')
            self.pvlist['diode_pwr_lolo'] = Pv(atca_base[self.name]+'DIODE_PWR'+'.LOLO')
            self.pvlist['diode_pwr_hihi'] = Pv(atca_base[self.name]+'DIODE_PWR'+'.HIHI')
        else:
            self.pvlist['phase_motor_dmov'] = Pv(phase_motor[self.name]+'.DMOV')  # motor motion status
        pass        

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

    