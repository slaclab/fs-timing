# femto_config.json description

## ReadMe
#### Version : V.1.0
#### Author : J.May
#### Initial Date : 2021-04-07

The femto_config.json format, represented in [template_femto_config.json](./template_femto_config.json), defines a structure for describing a given laser configuration for use with Femto.py (version 1.x). The contents are as follows:

```{
    "config_meta" : {
        "author" : "Justin May",
        "author_date" : "2021-04-07",
        "desc" : "This is a reference template configuration file for use with femto.py v1.1"
    },
    "config" : {
        "nm" : "replace with system identifier",
        "genpv_base" : "forms the initial pv base string for derived (incremented) PVs",
        "dev_base" : "in case this is different from base",
        "matlab_pv_base" : "again, change this if different; commonly dev_base + 'matlab'",
        "matlab_pv_offsets" : 1,
        "matlab_pv_digits" : 2,
        "counter_base" : "",
        "freq_counter" : "",
        "phase_motor" : "",
        "error_pv_name" : "",
        "version_pv_name" : "",
        "laser_trigger" : "",
        "trig_in_ticks" : "",
        "reverse_counter" : 1,
        "use_secondary_calibration" : false,
        "use_drift_correction" : false,
        "use_dither" : false,
        "timeout" : 1.0
        "feedback_delay" = 0.1 
            pvname = 'DEV:TIMETOOL:TTALL'  # time tool array name
            matlab_start = 20 # first matlab pv
            matlab_prefix = 'DEV:VIT:matlab:'  # start of matlab names
            stagename = 'DEV:DELAYSTAGE'  # delay stage for time tool
            ipmname = 'DEV:PULSEENERGY' # intensity profile monitor PV
            pixscale = 2.0e-6
            pcavset = "SXR"
    },
    "add_config" : {
        "feedback_delay" : 0.1, 
        "tt_pvname" : 'DEV:TIMETOOL:TTALL',
        "fb_matlab_start" : 20
            matlab_prefix = 'DEV:VIT:matlab:'  # start of matlab names
            stagename = 'DEV:DELAYSTAGE'  # delay stage for time tool
            ipmname = 'DEV:PULSEENERGY' # intensity profile monitor PV
            pixscale = 2.0e-6
            pcavset = "SXR"
    }
}
```  

The `config_meta` section includes author and creation information for the
configuration file, to be provided by said author. The description field should
be used for comments and additional information as desired.

The `config` section holds the primary configuration information for the
installation. This represents the base set of pvs that and control constants
that is needed to run a laser locker. Additional feedback parameters, and system
specific values should not be included here. Any error or ommission of a
parameter in the `config` section should result in an error case in femto.py.

The `add_config` section, for 'additional configuration', contains PVs or
assignments that are specific to an installation but which are not necessary for
operation of the locker, and as such do not result in a fail state in the
control software. An absence of a key in this dictionary is taken to mean that
the subsystem dependent on that key is not active, or operates in the default
mode of operation for that subsystem.

Keys in the `add_config` section will often be used by accessory code, typically
various forms of feedbacks that tie the laser locker and femto.py to other
systems like the xray/optical cross correlator or phase cavities.

## Notes on specific key/value pairs in the config dictionary

## Available `add_config` keys

| Key                    | Desc                                                                                                                                                                             | "Default"  | Acceptable Values                    | Type   |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------|--------------------------------------|--------|
| feedback_delay         | This is the internal wait time for processing the feedback function input to the laser phase control                                                                             | 0.1        | Typically anywhere from 0.1 to 1 Hz  | float  |
| tt_pvname              | `DEV:TIMETOOL:TTALL`; PV string for the packaged timetool waveform, appropriate for an installation                                                                              | n/a        | n/a                                  | str    |
| fb_matlab_start        | The default starting address in matlab/notepad pvs for the processed feedback data                                                                                               | 20         |                                      | int    |
| fb_matlab_prefix       | `DEV:VIT:matlab:` the pv string to prefix matlab/notepad pvs                                                                                                                     | n/a        | n/a                                  | str    |
| tt_stagename           | `DEV:DELAYSTAGE` PV for the timetool delay stage                                                                                                                                 | n/a        | n/a                                  | str    |
| tt_ipname              | `DEV:PULSEENERGY` PV for the intensity monitor (I think)                                                                                                                         | n/a        | n/a                                  | str    |
| tt_pixscale            | PV for the the detector output scaling, in case the output from the DAQ is not scaled correctly (ie. Generally would be unity, except for misconfigurations on the DAQ/TT side)  | 0.000002   |                                      | float  |
| pcavset                | Which phase cavity set should be used for arrival time tracking                                                                                                                  | SXR        | {SXR, HXR}                           | str    |
| secondary_calibration  | `DEV:INPUTPV` This is a PV used for the secondary calibration system, generally deprecated but left in for backwards compatibility                                               | n/a        | n/a                                  | str    |
