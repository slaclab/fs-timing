# fsmanager_gui Help

FSManager, for FemtoSecond (Timing) Manager, is an interface to the feedbacks that adjust the rf reference distributed to the near and far experimental hall, the high precision phase cavities, and which therefore controls XTCAV.

There are four phase cavities on each beamline, two each which are designed around an operational frequency of 2856 MHz (plus an offset) for monitoring the 120 Hz Normal Conducting (copper) linac. The output of the pcav system is shown under the area "Phase Cavities". If these values are not updating, first verify there are electrons at that location. If there are, then the system likely needs attention, contact either Justin May, Matt Weaver or Charlie Xu.

The measured PCAV arrival time is used as the input to modulate the rf reference for the experiments. However, this reference also is the source of the local oscillator for the phase cavity system. This is intentional, and means that the cable stabilizer phase control needs to act in a relative sense to minimize the motion of phase cavities while responding to what the accelerator is actually doing. Internal to the feedback is the actual signal conditioning, but two controls are provided at the UI level:

- Offset: the relative zero point for the pcavs; this is provided for resetting the offset, for instance after a period of downtime or program change
- Gain: an simple scaling term to adjust the strength of the feedback; in general won't be changed
- Enable/Disable: turn on/off the feedbacks, important when running multi-bunch patterns on a beamline that result in modulated pcav outputs

For more information about this system, see: [Femto-Second Timing on Confluence](https://confluence.slac.stanford.edu/display/PCDS/Phase+Cavity+System) (Pending revision)

____
Version: 1.0  
Author: Justin May  
Date: 2021-02-27  