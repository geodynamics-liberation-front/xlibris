#!/usr/bin/env python
import atexit
import sys
import os
import unittest
source = os.path.abspath("../src")
sys.path=[source]+sys.path

def remove_pyc():
    os.unlink(os.path.join(source,'scripts','xlibrisc'))
    for d,child_dir,files in os.walk(source):
        for f in [f for f in files if f.endswith("pyc")]:
            os.unlink(os.path.join(d,f))

if __name__== '__main__':
    atexit.register(remove_pyc)
    remove_pyc()
    import xlibris as xl
    xl.debug_on()

    import xlibris.settings as xlsettings
    import cases
    cases.settings = xlsettings.get_settings("settings.py")
    cases.settings.source=source

    from cases import test_lazy_collections
    from cases import test_import
    suite_lc=test_lazy_collections.get_suite()
    suite_i=test_import.get_suite()

    alltests = unittest.TestSuite([suite_lc, suite_i])
    unittest.TextTestRunner().run(alltests)


