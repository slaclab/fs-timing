""" A class designed to manage PV connections. It includes functions for setting
and getting values, and is written closely linked to the femtoconfig
configuration object. In most cases, the configuration that is loaded as part of
instantiating a PVS object is used throughout operation of the HLA. 

Justin May
"""

# try:
#     from psp.Pv import Pv 
#     print('using psp.Pv')
# except ModuleNotFoundError:
try:
    from epics.pv import PV as Pv
    # print('using epics.pv')
except ModuleNotFoundError:
    print('no epics pv support located within environment')
from numpy import log

from support.femtoconfig import Config
from support.ErrorOutput import error_output

class PVS():   # creates pvs
    """ Base PV class.
    
    This is the base class that organizes the PVs for operation of the code.
    It has been propagated forward to use the external configuration object.
    """

    def __init__(self, configfpath='femto_config.json', epicsdebug=False,localdebug=False):
        """ Initiate connections to PVs based on config.
        
        This function calls the various functions in femtoconfig.py to expand a
        configuration definition.
        
        Arguments:
        configfpath -- path to a configuration file, provided at launch of femto.py
        epicsdebug -- boolean value for whether to write errors to epics
        localdebug -- boolean value for whether to print errors to local
        """

        self.localLogLvl = 0
        if localdebug:
            self.localLogLvl = 2
        self.epicsLogLvl = 0
        if epicsdebug:
            self.epicsLogLvl = 1
        self.config = Config()
        self.config.readConfig(configfpath)
        self.config.expandPVs()
        timeout = self.config.timeout
        self.error_pv = self.config.error_pv
        self.error_pv.connect(timeout)
        self.E = error_output(self.error_pv,self.epicsLogLvl,self.localLogLvl)
        self.E.write_error({'value':'Watchdog 141126a','lvl':2})
        self.version = self.config.version
        self.name = self.config.name
        print(self.name)
        self.E.write_error({'value':'OK','lvl':2})
        # The following is left in place for reference to previous implementations
        # set up all the matlab PVs
        # for k, v in matlab_list.iteritems():  # loop over items
        #     if not matlab_use[matlab_list[k][0]]: #not overriding on this one, keep older pv.
        #         continue
        #     pvname = matlab_pv_base[self.name]+str(matlab_list[k][0]+matlab_pv_offset[self.name]).zfill(matlab_pv_digits[self.name])
        #     pv_description_field_name = pvname + '.DESC' # name of description field
        #     pv = Pv(pv_description_field_name)
        #     pv.connect(timeout)
        #     pv.put(value= self.name+' '+v[1], timeout=1.0) # put in the description field
        #     pv.disconnect() # done with this pv
        #     pv_prec_name = pvname + '.PREC' # precision field
        #     pv = Pv(pv_prec_name)
        #     pv.connect(timeout)
        #     pv.put(value = 4, timeout = 1.0) # set precision field
        #     pv.disconnect() # done with precision field
        #     self.pvlist[k]=Pv(pvname) # add pv  to list - this is where matlab woudl overwrite ioc pvs. 
        self.OK = 1   
        for k, v in iter(self.config.pvlist.items()):  # now loop over all pvs to initialize
            try:
                v.connect(timeout) # connect to pv
                v.get(with_ctrlvars=False, timeout=1.0) # get data
            except: # for now just fake it
                self.E.write_error({'value':'could not open '+v.__str__(),'lvl':2})
                self.E.write_error({'value':k,'lvl':2})
                self.OK = 0 # some error with setting up PVs, can't run, will exit  
        self.E.write_error({'value':'finished initial pv creation and connection','lvl':2})
        self.version_pv = self.config.version_pv
        self.version_pv.connect(timeout)
        self.version_pv.put(self.version, timeout = 10.0)
       
    def get(self, name):
        """ Epics get the requested pv by config name.
        
        This fetches a value from the supplied PV and returns it or an error.
        
        Arguments:
        name -- name of the pv created in femtoconfig
        """

        try:
            self.config.pvlist[name].get(with_ctrlvars=False, timeout=10.0)
            return self.config.pvlist[name].value                      
        except:
            self.E.write_error({'value':'PV READ ERROR','lvl':2})
            self.E.write_error({'value':name,'lvl':2})
            return 0
                         
    def get_last(self, name):
        """ Return the most recent fetched value for a PV name

        This function will return the most recent value that has been fetched
        for a pv (by femtoconfig name) in lieu of issuing a channel access call.

        Arguments:
        name -- name of the pv created in femtoconfig
        """

        return self.config.pvlist[name].value                
                
    def put(self, name, x):
        """ Write a value to a pv by femtoconfig name
        
        This function will issue a channel access call to write a value to a pv
        based on the name as defined in femtoconfig.
        
        Arguments:
        name -- name of the pv created in femtoconfig
        x -- value to write to pv in string format
        """

        try:
            self.config.pvlist[name].put(x, timeout = 10.0) # long timeout           
        except:
            self.E.write_error({'value':'UNABLE TO WRITE PV','lvl':2})
            self.E.write_error({'value':name,'lvl':2})
            self.E.write_error({'value':str(x),'lvl':2})
                
    def __del__ (self):
        """ Clear connections to pvs
        
        This function is reimplemented from the original HLA, but is not used as
        much now, in part because it never really worked that well before, so
        the original version of femto.py had written much of this out. It works
        now, using the mechanism built into our standard epics support.
        """

        for v in iter(self.config.pvlist.values()):
            v.disconnect()  
        self.error_pv.disconnect()    
        self.E.write_error({'value':'closed all PV connections','lvl':2})
