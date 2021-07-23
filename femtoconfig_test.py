"""femtoconfig tests"""

import femtoconfig
import unittest
import og_pvs

class Test_testReadConfig(unittest.TestCase):
    def test_invalidPathName(self):
        self.assertRaises(OSError,femtoconfig.Config().readConfig('test'))

class Test_pvconfigmatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tconf = femtoconfig.Config()
        tconf.readConfig("configs/astagen1.json")
        tconf.expandPVs()
        refconf = og_pvs.PVS("ASTA")

    def test_versionstring(self):
        self.assertEqual(tconf.name, refconf.name)