#!/usr/bin/env python
"""
Start or stop transmission from one or more ROACHs.

@author: paulp
"""
import argparse
import os

from casperfpga import utils as fpgautils
from casperfpga import katcp_fpga
from casperfpga import dcp_fpga
from corr2 import utils

parser = argparse.ArgumentParser(
    description='Start or stop 10gbe transmission on a CASPER device',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument(
    '--hosts', dest='hosts', type=str, action='store', default='',
    help='comma-delimited list of hosts, or a corr2 config file')
parser.add_argument(
    '--class', dest='hclass', action='store', default='',
    help='start/stop a class: fengine or xengine')
parser.add_argument(
    '--start', dest='start', action='store_true', default=False,
    help='start TX')
parser.add_argument(
    '--stop', dest='stop', action='store_true', default=False,
    help='stop TX')
parser.add_argument(
    '--comms', dest='comms', action='store', default='katcp', type=str,
    help='katcp (default) or dcp?')
parser.add_argument(
    '--loglevel', dest='log_level', action='store', default='',
    help='log level to use, default None, options INFO, DEBUG, ERROR')
parser.add_argument(
    '--listhosts', dest='listhosts', action='store_true', default=False,
    help='list hosts and exit')
args = parser.parse_args()

if not (args.stop or args.start):
    print 'Cowardly refusing to do nothing!'
else:
    if args.log_level:
        import logging
        log_level = args.log_level.strip()
        try:
            logging.basicConfig(level=getattr(logging, log_level))
        except AttributeError:
            raise RuntimeError('No such log level: %s' % log_level)

    if args.comms == 'katcp':
        HOSTCLASS = katcp_fpga.KatcpFpga
    else:
        HOSTCLASS = dcp_fpga.DcpFpga

    # are we doing it by class?
    if 'CORR2INI' in os.environ.keys() and args.hosts == '':
        args.hosts = os.environ['CORR2INI']
    if args.hclass != '':
        if args.hclass == 'fengine':
            hosts = utils.parse_hosts(args.hosts, section='fengine')
        elif args.hclass == 'xengine':
            hosts = utils.parse_hosts(args.hosts, section='xengine')
        else:
            raise RuntimeError('No such host class: %s' % args.hclass)
    else:
        hosts = utils.parse_hosts(args.hosts)
    if len(hosts) == 0:
        raise RuntimeError('No good carrying on without hosts.')

    if args.listhosts:
        print hosts
        import sys
        sys.exit()

    # create the devices and start/stop tx
    fpgas = fpgautils.threaded_create_fpgas_from_hosts(HOSTCLASS, hosts)
    fpgautils.threaded_fpga_function(fpgas, 10, 'get_system_information')


    def start_stop(stopstart):
        print '%s tx on all hosts' % ('Starting' if stopstart else 'Stopping')
        if fpgas[0].registers.names().count('control') > 0:
            if fpgas[0].registers.control.field_names().count('gbe_out_en') > 0:
                print '\tProduction control registers found.'
                fpgautils.threaded_fpga_operation(
                    fpgas, 10,
                    lambda fpga: fpga.registers.control.write(
                        gbe_out_en=stopstart))
            elif fpgas[0].registers.control.field_names().count('gbe_txen') > 0:
                print '\tSim-style control registers found.'
                fpgautils.threaded_fpga_operation(
                    fpgas, 10,
                    lambda fpga: fpga.registers.control.write(
                        gbe_txen=stopstart))
            elif fpgas[0].registers.control.field_names().count('comms_en') > 0:
                print '\tOld-style control registers found.'
                fpgautils.threaded_fpga_operation(
                    fpgas, 10,
                    lambda fpga: fpga.registers.control.write(
                        comms_en=stopstart))
        elif fpgas[0].registers.names().count('ctrl') > 0:
            if fpgas[0].registers.ctrl.field_names().count('comms_en') > 0:
                print '\tSome control registers found?'
                print fpgautils.threaded_fpga_operation(
                    fpgas, 10,
                    lambda fpga: fpga.registers.ctrl.write(comms_en=stopstart))
        else:
            print '\tCould not find the correct registers to control TX'

    # stop
    if args.stop:
        start_stop(False)

    # start
    if args.start:
        start_stop(True)

    fpgautils.threaded_fpga_function(fpgas, 10, 'disconnect')

# end
