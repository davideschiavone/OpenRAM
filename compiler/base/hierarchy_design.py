# See LICENSE for licensing information.
#
# Copyright (c) 2016-2019 Regents of the University of California and The Board
# of Regents for the Oklahoma Agricultural and Mechanical College
# (acting for and on behalf of Oklahoma State University)
# All rights reserved.
#
import hierarchy_layout
import hierarchy_spice
import debug
import os
from globals import OPTS
import tech


class hierarchy_design(hierarchy_spice.spice, hierarchy_layout.layout):
    """
    Design Class for all modules to inherit the base features.
    Class consisting of a set of modules and instances of these modules
    """
    name_map = []

    def __init__(self, name, cell_name):
        self.gds_file = OPTS.openram_tech + "gds_lib/" + cell_name + ".gds"
        self.sp_file = OPTS.openram_tech + "sp_lib/" + cell_name + ".sp"

        # If we have a separate lvs directory, then all the lvs files
        # should be in there (all or nothing!)
        try:
            lvs_subdir = tech.lvs_lib
        except AttributeError:
            lvs_subdir = "lvs_lib"
        lvs_dir = OPTS.openram_tech + lvs_subdir + "/"

        if os.path.exists(lvs_dir):
            self.lvs_file = lvs_dir + cell_name + ".sp"
        else:
            self.lvs_file = self.sp_file

        self.drc_errors = "skipped"
        self.lvs_errors = "skipped"

        self.name = name
        self.cell_name = cell_name
        hierarchy_spice.spice.__init__(self, name, cell_name)
        hierarchy_layout.layout.__init__(self, name, cell_name)
        self.init_graph_params()

    def get_layout_pins(self, inst):
        """ Return a map of pin locations of the instance offset """
        # find the instance
        for i in self.insts:
            if i.name == inst.name:
                break
        else:
            debug.error("Couldn't find instance {0}".format(inst.name), -1)
        inst_map = inst.mod.pin_map
        return inst_map

    def DRC_LVS(self, final_verification=False, force_check=False):
        """Checks both DRC and LVS for a module"""
        import verify

        # No layout to check
        if OPTS.netlist_only:
            return
        # Unit tests will check themselves.
        elif not force_check and OPTS.is_unit_test:
            return
        elif not force_check and not OPTS.check_lvsdrc:
            return
        # Do not run if disabled in options.
        elif (OPTS.inline_lvsdrc or force_check or final_verification):

            tempspice = "{0}/{1}.sp".format(OPTS.openram_temp, self.name)
            tempgds = "{0}/{1}.gds".format(OPTS.openram_temp, self.name)
            self.lvs_write(tempspice)
            self.gds_write(tempgds)
            # Final verification option does not allow nets to be connected by label.
            self.drc_errors = verify.run_drc(self.cell_name, tempgds, extract=True, final_verification=final_verification)
            self.lvs_errors = verify.run_lvs(self.cell_name, tempgds, tempspice, final_verification=final_verification)

            # force_check is used to determine decoder height and other things, so we shouldn't fail
            # if that flag is set
            if OPTS.inline_lvsdrc and not force_check:
                debug.check(self.drc_errors == 0,
                            "DRC failed for {0} with {1} error(s)".format(self.cell_name,
                                                                          self.drc_errors))
                debug.check(self.lvs_errors == 0,
                            "LVS failed for {0} with {1} errors(s)".format(self.cell_name,
                                                                           self.lvs_errors))

            if OPTS.purge_temp:
                os.remove(tempspice)
                os.remove(tempgds)

    def DRC(self, final_verification=False):
        """Checks DRC for a module"""
        import verify

        # Unit tests will check themselves.
        # Do not run if disabled in options.

        # No layout to check
        if OPTS.netlist_only:
            return
        elif (not OPTS.is_unit_test and OPTS.check_lvsdrc and (OPTS.inline_lvsdrc or final_verification)):
            tempgds = "{0}/{1}.gds".format(OPTS.openram_temp, self.cell_name)
            self.gds_write(tempgds)
            num_errors = verify.run_drc(self.cell_name, tempgds, final_verification=final_verification)
            debug.check(num_errors == 0,
                        "DRC failed for {0} with {1} error(s)".format(self.cell_name,
                                                                      num_errors))

            if OPTS.purge_temp:
                os.remove(tempgds)

    def LVS(self, final_verification=False):
        """Checks LVS for a module"""
        import verify

        # Unit tests will check themselves.
        # Do not run if disabled in options.

        # No layout to check
        if OPTS.netlist_only:
            return
        elif (not OPTS.is_unit_test and OPTS.check_lvsdrc and (OPTS.inline_lvsdrc or final_verification)):
            tempspice = "{0}/{1}.sp".format(OPTS.openram_temp, self.cell_name)
            tempgds = "{0}/{1}.gds".format(OPTS.openram_temp, self.name)
            self.lvs_write(tempspice)
            self.gds_write(tempgds)
            num_errors = verify.run_lvs(self.name, tempgds, tempspice, final_verification=final_verification)
            debug.check(num_errors == 0,
                        "LVS failed for {0} with {1} error(s)".format(self.cell_name,
                                                                      num_errors))
            if OPTS.purge_temp:
                os.remove(tempspice)
                os.remove(tempgds)

    def init_graph_params(self):
        """
        Initializes parameters relevant to the graph creation
        """
        # Only initializes a set for checking instances which should not be added
        self.graph_inst_exclude = set()

    def build_graph(self, graph, inst_name, port_nets):
        """
        Recursively create graph from instances in module.
        """

        # Translate port names to external nets
        if len(port_nets) != len(self.pins):
            debug.error("Port length mismatch:\nExt nets={}, Ports={}".format(port_nets,
                                                                              self.pins),
                        1)
        port_dict = {pin: port for pin, port in zip(self.pins, port_nets)}
        debug.info(3, "Instance name={}".format(inst_name))
        for subinst, conns in zip(self.insts, self.conns):
            if subinst in self.graph_inst_exclude:
                continue
            subinst_name = inst_name + '.X' + subinst.name
            subinst_ports = self.translate_nets(conns, port_dict, inst_name)
            subinst.mod.build_graph(graph, subinst_name, subinst_ports)

    def build_names(self, name_dict, inst_name, port_nets):
        """
        Collects all the nets and the parent inst of that net.
        """
        # Translate port names to external nets
        if len(port_nets) != len(self.pins):
            debug.error("Port length mismatch:\nExt nets={}, Ports={}".format(port_nets,
                                                                              self.pins),
                        1)
        port_dict = {pin: port for pin, port in zip(self.pins, port_nets)}
        debug.info(3, "Instance name={}".format(inst_name))
        for subinst, conns in zip(self.insts, self.conns):
            subinst_name = inst_name + '.X' + subinst.name
            subinst_ports = self.translate_nets(conns, port_dict, inst_name)
            for si_port, conn in zip(subinst_ports, conns):
                # Only add for first occurrence
                if si_port.lower() not in name_dict:
                    mod_info = {'mod': self, 'int_net': conn}
                    name_dict[si_port.lower()] = mod_info
            subinst.mod.build_names(name_dict, subinst_name, subinst_ports)

    def translate_nets(self, subinst_ports, port_dict, inst_name):
        """
        Converts connection names to their spice hierarchy equivalent
        """
        converted_conns = []
        for conn in subinst_ports:
            if conn in port_dict:
                converted_conns.append(port_dict[conn])
            else:
                converted_conns.append("{}.{}".format(inst_name, conn))
        return converted_conns

    def add_graph_edges(self, graph, port_nets):
        """
        For every input, adds an edge to every output.
        Only intended to be used for gates and other simple modules.
        """
        # The final pin names will depend on the spice hierarchy, so
        # they are passed as an input.
        pin_dict = {pin: port for pin, port in zip(self.pins, port_nets)}
        input_pins = self.get_inputs()
        output_pins = self.get_outputs()
        inout_pins = self.get_inouts()
        for inp in input_pins + inout_pins:
            for out in output_pins + inout_pins:
                if inp != out: # do not add self loops
                    graph.add_edge(pin_dict[inp], pin_dict[out], self)

    def __str__(self):
        """ override print function output """
        pins = ",".join(self.pins)
        insts = ["    {}".format(x) for x in self.insts]
        objs = ["    {}".format(x) for x in self.objs]
        s = "********** design {0} **********".format(self.cell_name)
        s += "\n  pins ({0})={1}\n".format(len(self.pins), pins)
        s += "\n  objs ({0})=\n{1}\n".format(len(self.objs), "\n".join(objs))
        s += "\n  insts ({0})=\n{1}\n".format(len(self.insts), "\n".join(insts))
        return s

    def __repr__(self):
        """ override print function output """
        text="( design: " + self.name + " pins=" + str(self.pins) + " " + str(self.width) + "x" + str(self.height) + " )\n"
        for i in self.objs:
            text+=str(i) + ",\n"
        for i in self.insts:
            text+=str(i) + ",\n"
        return text

