try:
    from psp.Pv import Pv 
    print('using psp.Pv')
except ModuleNotFoundError:
    try:
        from epics.pv import PV as Pv
        print('using epics.pv')
    except ModuleNotFoundError:
        print('no epics pv support located within environment')

from support.femtoconfig import Config
from support.ErrorOutput import error_output

class PVS():   # creates pvs
    """ This is the base class that organizes the PVs for operation of the code.
    It has been propagated forward to use the external configuration object"""
    def __init__(self, configfpath='femto_config.json', debug=False):
        if debug:
            print('creating PVS object')
        self.config = Config()
        self.config.readConfig(configfpath)
        self.config.expandPVs()
        # self.version = 'Watchdog 141126a' # version string
        self.version = self.config.version
        self.name = self.config.name
        print(self.name)
        timeout = self.config.timeout

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
                # print(k,v)
                v.connect(timeout) # connect to pv
                v.get(with_ctrlvars=True, timeout=1.0) # get data
                
            except: # for now just fake it
                print('could not open '+v.__str__())
                print(k)
                self.OK = 0 # some error with setting up PVs, can't run, will exit  
        if debug:
            print('finished initial pv creation and connection')
        self.error_pv = self.config.error_pv
        self.error_pv.connect(timeout)
        self.version_pv = self.config.version_pv
        self.version_pv.connect(timeout)
        self.version_pv.put(self.version, timeout = 10.0)
        self.E = error_output(self.error_pv)
        self.E.write_error('OK')
       
    def get(self, name):
        try:
            self.pvlist[name].get(with_ctrlvars=True, timeout=10.0)
            return self.pvlist[name].value                      
        except:
            print('PV READ ERROR')
            print(name)
            return 0
                         
    def get_last(self, name): # gets last value read, no pv read / write
        return self.pvlist[name].value                
                
    def put(self, name, x):
        try:
            self.pvlist[name].put(x, timeout = 10.0) # long timeout           
        except:
            print('UNABLE TO WRITE PV')
            print(name)
            print(x)
                
    def __del__ (self):
        for v in self.pvlist.itervalues():
            v.disconnect()  
        self.error_pv.disconnect()    
        print('closed all PV connections')