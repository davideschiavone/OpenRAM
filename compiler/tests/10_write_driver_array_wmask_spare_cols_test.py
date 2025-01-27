#!/usr/bin/env python3
# See LICENSE for licensing information.
#
# Copyright (c) 2016-2021 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import unittest
from testutils import *
import sys, os


import globals
from globals import OPTS
from sram_factory import factory
import debug


class write_driver_array_wmask_spare_cols_test(openram_test):

    def runTest(self):
        config_file = "{}/tests/configs/config".format(os.getenv("OPENRAM_HOME"))
        globals.init_openram(config_file)

        # check write driver array for single port
        debug.info(2, "Testing write_driver_array for columns=8, word_size=8, write_size=4")
        a = factory.create(module_type="write_driver_array", columns=8, word_size=8, write_size=4, num_spare_cols=3)
        self.local_check(a)

        debug.info(2, "Testing write_driver_array for columns=16, word_size=16, write_size=2")
        a = factory.create(module_type="write_driver_array", columns=16, word_size=16, write_size=2, num_spare_cols=2)
        self.local_check(a)

        debug.info(2, "Testing write_driver_array for columns=16, word_size=8, write_size=4")
        a = factory.create(module_type="write_driver_array", columns=16, word_size=8, write_size=4, num_spare_cols=3)
        self.local_check(a)

        globals.end_openram()


# run the test from the command line
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    header(__file__, OPTS.tech_name)
    unittest.main(testRunner=debugTestRunner())
