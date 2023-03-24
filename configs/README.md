# ReadMe  
#### Version : V.1.o  
#### Author : J.May  
#### Initial Date : 2023-03-20  

## Contents  
* Readme - Documentation covering the creation and use of the configuration file.  
* SampleConfiguration.json - A sample configuration file for use with femto.py.  

## Overview  
The configuration file is a major change to the design of Femto.py. The original version of the HLA had pv values hard-coded for every installation across facility areas. Combined with a lack of version control, this resulted in a great deal of version divergence in installations. Femto.py has since been re-written to read in a configuration file via a command line argument. The configuration files themselves are masked from the repository, so the user can feel free to place their own configuration files in the folder this folder when it is created by, for example, cloning this repository. A reference template is provided in support/templates/. 

## Description of Fields  

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

### Header: **config_meta**  

| field       | type | desc                                                                                                                                                         | Example or Possible Values |
| ----------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------- |
| author      | str  | author meta data for the configuration.                                                                                                                      |                            |
| author_date | str  | meta data for date of authoring                                                                                                                              |                            |
| desc        | str  | description meta data for the configuration; can be modified to have some element of design history, but ideally these should be tracked in version control. |                            |

### Header: **config**  

| field                     | type  | desc                                                                                                                                                                                                                                                                                                                      | Example or Possible Values |
| ------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| name                      | str   | A descriptive name displayed during launch; the original femto.py used a name string to load a selection of hard-coded values, but the functionality of the refactored femto.py intentionally removes the dependence on a string. It is best to use something that makes sense to the maintainer of a given installation. |                            |
| genpv_base                | str   | Base PV string. The specific PVs for the system will get appended to this.                                                                                                                                                                                                                                                |                            |
| dev_base                  | str   | An alternate base string for devices used in the code to build pvs addresses for physical devices. These are often external to the vitara-derived ioc, and hence have alternate names.                                                                                                                                    |                            |
| matlab_pv_base            | str   | This is a legacy pv field that in most cases can be omitted, but is included for legacy support. New installations should not use matlab/notepad pvs unless absolutely necessary, in which case this field should contain the common prefix path up to the total length minus the value in "matlab_pv_digits" (below)     |                            |
| matlab_pv_offsets         | int   | This is a legacy pv field that in most cases can be omitted, but is included for legacy support. If used, this should contain the starting index for matlab/notepad pvs. The length should match the number of digits provided in "matlab_pv_digits" (below).                                                             |                            |
| matlab_pv_digits          | int   | The is a legacy pv field that in most cases can be omitted, but is included for legacy support. If used, this field should include the number of digits that should be incremented.                                                                                                                                       |                            |
| counter_base              | str   | Base pv string for the time interval counter supporting the installation.                                                                                                                                                                                                                                                 |                            |
| freq_counter              | str   | Base pv string for the frequency counter supporting the installation.                                                                                                                                                                                                                                                     |                            |
| phase_motor               | str   | PV address for the phase motor control.                                                                                                                                                                                                                                                                                   |                            |
| error_pv_name             | str   | PV address to which elevated error messages should be directed.                                                                                                                                                                                                                                                           |                            |
| version_pv_name           | str   | PV used to report version information (deprecated).                                                                                                                                                                                                                                                                       |                            |
| laser_trigger             | str   | PV String for the laser output trigger (that which is triggering an SDG or AOM, for example).                                                                                                                                                                                                                             |                            |
| trig_in_ticks             | int   | Boolean value (JSON False or 0) that indicates whether the trigger control should be in ticks or time. Most systems will use time (ie. a value of "false").                                                                                                                                                               |                            |
| reverse_counter           | int   | Boolean value that indicates whether Time Interval Counter (TIC) measurements should be reversed, matching the A-B configuration of the TIC. In most configurations, this should be "true" or 1.                                                                                                                          |                            |
| use_secondary_calibration | int   | Boolean value that indicates whether an experimental secondary calibration should be used. This is largely for legacy support, and was only originally used on a limited selection of LCLS hutches.                                                                                                                       |                            |
| use_drift_correction      | bool  | Boolean value that indicates whether external feedback values should be included in drift correction of the laser output time. This is slated for further development, but at this point is included for legacy support for LCLS hutches utilizing X-Ray/Optical Cross-Correlator Data.                                   |                            |
| use_dither                | bool  | Boolean value for whether a temporal dither should be used with the laser. Provided largely for legacy support, current systems do not utilize this field.                                                                                                                                                                |                            |
| timeout                   | float | Value for EPICS pv timeout.                                                                                                                                                                                                                                                                                               |                            |
| atca                      | bool  |                                                                                                                                                                                                                                                                                                                           |                            |
| type                      | str   | An identifier for the type of laser system that is being run. Possible values are {"SIM","ATCA"}                                                                                                                                                                                                                          |                            |

### Header: **add_config**  

| field          | type  | desc                                                                                                                                                                                                                                                                                                                                        | Example or Possible Values |
| -------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| feedback_delay | float |                                                                                                                                                                                                                                                                                                                                             |                            |
| usetimetool    | bool  |                                                                                                                                                                                                                                                                                                                                             |                            |
| usepcav        | bool  |                                                                                                                                                                                                                                                                                                                                             |                            |
| pcavset        | str   |                                                                                                                                                                                                                                                                                                                                             |                            |
| pixscale       | float |                                                                                                                                                                                                                                                                                                                                             |                            |
| tic_type       | str   | A string which can be used to indicate an alternate model of Time Interval Counter. Support is currently provided for the Keysight 53220/53230 Model of counter, which necessitates a different approach to handling buffers and mode switching, but in most installations an SR620 is still used, in which case this field can be omitted. |                            |



## Version History  
1.0
- Initial version of documentation  