import re
# from Tkinter import Tk

srcstring = "\tdef test_pv_$1_match_CONDITIONAL(self):\n\t\tif not self.refconf.reverse_counter:\n\t\t\tself.assertEqual(self.tconf.pvlist['$1'],self.refconf.pvlist['$1'])\n\n"
exportstring = ""
srcdata = ["self.pvlist['counter'] = Pv(counter_base[self.name]+'GetMeasMean')  #time interval counter result, create Pv",
            "self.pvlist['counter_low'] = Pv(counter_base[self.name]+'GetMeasMean.LOW')        ",
            "self.pvlist['counter_high'] = Pv(counter_base[self.name]+'GetMeasMean.HIGH')"]
            
for entry in srcdata:
    matches = re.search("(?<=self.pvlist\[')(.*)(?='\].*)",entry)
    exportstring = exportstring + re.sub("\$1",matches.group(0),srcstring)

print(exportstring)