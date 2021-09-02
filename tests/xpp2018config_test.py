"""femtoconfig tests"""

import femtoconfig
import unittest
import og_pvs

class test_testReadConfig(unittest.TestCase):
    def test_invalidPathName(self):
        self.assertRaises(TypeError,femtoconfig.Config().readConfig('test'))

class test_pvconfigmatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tconf = femtoconfig.Config()
        cls.tconf.readConfig("configs/xpp_2018.json")
        cls.tconf.expandPVs()
        cls.refconfname = "XPP"
        cls.refconf = og_pvs.PVS(cls.refconfname)

    def test_name_match(self):
        self.assertEqual(self.tconf.name, self.refconf.name)

    def test_use_secondary_calibration_match(self):
        self.assertEqual(self.tconf.use_secondary_calibration, self.refconf.use_secondary_calibration)
    
    def test_is_atca_match(self):
        # previous versions of femto py try/catched this, supporting this on the
        # old systems is not necessary, so passing on this config until we roll
        # out more new systems.
        # try:
        #     self.assertEqual(self.tconf.is_atca,self.refconf.is_atca)
        # except AttributeError:
        #     self.assertFalse(self.tconf.is_atca)
        pass

    def test_use_drift_correction_match(self):
        self.assertEqual(self.tconf.use_drift_correction,self.refconf.use_drift_correction)
        
    def test_drift_correction_multiplier_matches_CONDITIONAL(self):
        if self.refconf.use_drift_correction:
            self.assertEqual(self.tconf.drift_correction_multiplier,self.refconf.drift_correction_multiplier)
        else:
            pass

    def test_freq_counter_match(self):
        self.assertEqual(self.tconf.pvlist['freq_counter'], self.refconf.pvlist['freq_counter'])

    def test_use_dither_match(self):
        self.assertEqual(self.tconf.use_dither,self.refconf.use_dither)

    def test_dither_level_match_CONDITIONAL(self):
        if self.refconf.use_dither:
            self.assertEqual(self.tconf.pvlist['dither_level'],self.refconf.pvlist['dither_level'])
        else:
            pass

    def test_trig_in_tick_match(self):
        self.assertEqual(self.tconf.trig_in_ticks,self.refconf.trig_in_ticks)

    def test_reverse_counter_match(self):
        self.assertEqual(self.tconf.reverse_counter,self.refconf.reverse_counter)

    def test_pv_watchdog_match(self):
        self.assertEqual(self.tconf.pvlist['watchdog'],self.refconf.pvlist['watchdog'])

    def test_pv_oscillator_f_match(self):
        self.assertEqual(self.tconf.pvlist['oscillator_f'],self.refconf.pvlist['oscillator_f'])
    
    def test_pv_time_match(self):
        self.assertEqual(self.tconf.pvlist['time'],self.refconf.pvlist['time'])
    
    def test_pv_time_hihi_match(self):
        self.assertEqual(self.tconf.pvlist['time_hihi'],self.refconf.pvlist['time_hihi'])
    
    def test_pv_time_lolo_match(self):
        self.assertEqual(self.tconf.pvlist['time_lolo'],self.refconf.pvlist['time_lolo'])
    
    def test_pv_calibrate_match(self):
        self.assertEqual(self.tconf.pvlist['calibrate'],self.refconf.pvlist['calibrate'])
    
    def test_pv_enable_match(self):
        self.assertEqual(self.tconf.pvlist['enable'],self.refconf.pvlist['enable'])
    
    def test_pv_busy_match(self):
        self.assertEqual(self.tconf.pvlist['busy'],self.refconf.pvlist['busy'])
    
    def test_pv_error_match(self):
        self.assertEqual(self.tconf.pvlist['error'],self.refconf.pvlist['error'])
    
    def test_pv_ok_match(self):
        self.assertEqual(self.tconf.pvlist['ok'],self.refconf.pvlist['ok'])
    
    def test_pv_fix_bucket_match(self):
        self.assertEqual(self.tconf.pvlist['fix_bucket'],self.refconf.pvlist['fix_bucket'])
    
    def test_pv_delay_match(self):
        self.assertEqual(self.tconf.pvlist['delay'],self.refconf.pvlist['delay'])
    
    def test_pv_offset_match(self):
        self.assertEqual(self.tconf.pvlist['offset'],self.refconf.pvlist['offset'])
    
    def test_pv_enable_trig_match(self):
        self.assertEqual(self.tconf.pvlist['enable_trig'],self.refconf.pvlist['enable_trig'])
    
    def test_pv_bucket_error_match(self):
        self.assertEqual(self.tconf.pvlist['bucket_error'],self.refconf.pvlist['bucket_error'])
    
    def test_pv_bucket_counter_match(self):
        self.assertEqual(self.tconf.pvlist['bucket_counter'],self.refconf.pvlist['bucket_counter'])
    
    def test_pv_deg_Sband_match(self):
        self.assertEqual(self.tconf.pvlist['deg_Sband'],self.refconf.pvlist['deg_Sband'])
    
    def test_pv_deg_offset_match(self):
        self.assertEqual(self.tconf.pvlist['deg_offset'],self.refconf.pvlist['deg_offset'])
    
    def test_pv_ns_offset_match(self):
        self.assertEqual(self.tconf.pvlist['ns_offset'],self.refconf.pvlist['ns_offset'])
    
    def test_pv_calib_error_match(self):
        self.assertEqual(self.tconf.pvlist['calib_error'],self.refconf.pvlist['calib_error'])

    def test_pv_counter_match_CONDITIONAL(self):
        if self.refconf.reverse_counter:
            self.assertEqual(self.tconf.pvlist['counter'],self.refconf.pvlist['counter'])
        else:
            pass

    def test_pv_counter_low_match_CONDITIONAL(self):
        if self.refconf.reverse_counter:
            self.assertEqual(self.tconf.pvlist['counter_low'],self.refconf.pvlist['counter_low'])
        else:
            pass

    def test_pv_counter_high_match_CONDITIONAL(self):
        if self.refconf.reverse_counter:
            self.assertEqual(self.tconf.pvlist['counter_high'],self.refconf.pvlist['counter_high'])
        else:
            pass

    def test_pv_counter_match_CONDITIONAL(self):
        if not self.refconf.reverse_counter:
            self.assertEqual(self.tconf.pvlist['counter'],self.refconf.pvlist['counter'])
        else:
            pass

    def test_pv_counter_low_match_CONDITIONAL(self):
        if not self.refconf.reverse_counter:
            self.assertEqual(self.tconf.pvlist['counter_low'],self.refconf.pvlist['counter_low'])
        else:
            pass

    def test_pv_counter_high_match_CONDITIONAL(self):
        if not self.refconf.reverse_counter:
            self.assertEqual(self.tconf.pvlist['counter_high'],self.refconf.pvlist['counter_high'])
        else:
            pass

    def test_phase_motor_match(self):
        self.assertEqual(self.tconf.pvlist['phase_motor'],self.refconf.pvlist['phase_motor'])

    def test_error_pv_match(self):
        self.assertEqual(self.tconf.error_pv,self.refconf.error_pv)

    def test_version_pv_name_match(self):
        self.assertEqual(self.tconf.version_pv,self.refconf.version_pv)

    def test_laser_trigger_match(self):
        self.assertEqual(self.tconf.pvlist['laser_trigger'],self.refconf.pvlist['laser_trigger'])

    def test_matlab_pv_offsets_match(self):
        # This pv is not currently used in python-only installs
        # self.assertEqual(self.tconf.matlab_pv_offset,self.refconf.matlab_pv_offset)
        pass

    def test_matlab_pv_digits_match(self):
        # This pv is not currently used in python-only installs
        # self.assertEqual(self.tconf.matlab_pv_digits,self.refconf.matlab_pv_digits)
        pass

    def test_timeout_match(self):
        # Original PVS did not propagate timeout
        # self.assertEqual(self.tconf.timeout, self.refconf.timeout)
        pass

    def test_use_combined_counter_match(self):
        # None of the original systems yet use the combined function unit
        # self.assertEqual(self.tconf.use_combined_counter,self.refconf.use_combined_counter)
        pass

    def test_number_of_pvs_in_pvlist_match(self):
        # alist = []
        # blist = []
        # for entry in self.refconf.pvlist.keys():
        #     if entry not in self.tconf.pvlist.keys():
        #         alist.append(entry)
        # for entry in self.tconf.pvlist.keys():
        #     if entry not in self.refconf.pvlist.keys():
        #         blist.append(entry)
        # print(self.tconf.pvlist)
        # print("tconf missing",alist)
        # print("refconf missing",blist)
        self.assertEqual(len(self.tconf.pvlist),len(self.refconf.pvlist))