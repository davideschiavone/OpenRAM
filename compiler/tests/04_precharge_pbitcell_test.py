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

class precharge_pbitcell_test(openram_test):

    def runTest(self):
        config_file = "{}/tests/configs/config".format(os.getenv("OPENRAM_HOME"))
        globals.init_openram(config_file)

        # check precharge in multi-port
        OPTS.bitcell = "pbitcell"
        OPTS.num_rw_ports = 1
        OPTS.num_r_ports = 1
        OPTS.num_w_ports = 1

        factory.reset()
        debug.info(2, "Checking precharge for pbitcell (innermost connections)")
        tx = factory.create(module_type="precharge", size=1, bitcell_bl="bl0", bitcell_br="br0")
        self.local_check(tx)

        factory.reset()
        debug.info(2, "Checking precharge for pbitcell (innermost connections)")
        tx = factory.create(module_type="precharge", size=1, bitcell_bl="bl1", bitcell_br="br1")
        self.local_check(tx)

        factory.reset()
        debug.info(2, "Checking precharge for pbitcell (outermost connections)")
        tx = factory.create(module_type="precharge", size=1, bitcell_bl="bl2", bitcell_br="br2")
        self.local_check(tx)

        globals.end_openram()

# run the test from the command line
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    header(__file__, OPTS.tech_name)
    unittest.main(testRunner=debugTestRunner())
