import femtoconfig

testconf = femtoconfig.Config()
testconf.readConfig("template_femto_config.json")
testconf.printDefs()