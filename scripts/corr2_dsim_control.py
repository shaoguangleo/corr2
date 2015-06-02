__author__ = 'paulp'

import argparse
import sys
import time
import os
import ConfigParser

from casperfpga import tengbe

from corr2 import utils

from corr2.dsimhost_fpga import FpgaDsimHost

parser = argparse.ArgumentParser(description='Control the dsim-engine (fake digitiser.)',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--config', type=str, action='store', help=
                    'corr2 config file. (default: Use CORR2INI env var)')
parser.add_argument('--program', dest='program', action='store_true', default=False,
                    help='(re)program the fake digitiser')
parser.add_argument('--deprogram', dest='deprogram', action='store_true', default=False,
                    help='deprogram the fake digitiser')
parser.add_argument('--start', dest='start', action='store_true', default=False,
                    help='start the fake digitiser transmission')
parser.add_argument('--pulse', action='store_true', default=False, help=
                    'Send a pulse of fake packets. Does nothing if digitiser is '
                    'already transmitting, use --stop first. It will only work '
                    'once until the dsim-engine is reset, e.g using --resync '
                    'which can be used with --pulse (--resync will be applied first).')
parser.add_argument('--pulse-packets', action='store', default=100, help=
                    'Send out out this many data packets per polarisation if --pulse '
                    'is specified (default: %(default)d.')
parser.add_argument('--resync', action='store_true', default=False,
                    help='Restart digitiser time and then sync')
parser.add_argument('--stop', dest='stop', action='store_true', default=False,
                    help='stop the fake digitiser transmission')
parser.add_argument('--loglevel', dest='log_level', action='store', default='',
                    help='log level to use, default None, options INFO, DEBUG, ERROR')
parser.add_argument('--ipython', action='store_true', default=False, help=
                    'Launch an embedded ipython shell once all is said and done')
args = parser.parse_args()

if args.log_level != '':
    import logging
    log_level = args.log_level.strip()
    try:
        logging.basicConfig(level=eval('logging.%s' % log_level))
    except AttributeError:
        raise RuntimeError('No such log level: %s' % log_level)

if args.config:
    config_filename = args.config
else:
    try:
        config_filename = os.environ['CORR2INI']
    except KeyError:
        raise RuntimeError(
            'No config file speficied and environment var "CORR2INI" not defined')

corr_conf = utils.parse_ini_file(config_filename, ['dsimengine'])
dsim_conf = corr_conf['dsimengine']
dig_host = dsim_conf['host']

dhost = FpgaDsimHost(dig_host, config=dsim_conf)
print 'Connected to %s.' % dhost.host

if args.start and args.stop:
    raise RuntimeError('Start and stop? You must be crazy!')

something_happened = False
if args.program:
    dhost.initialise()
    something_happened = True
else:
    dhost.get_system_information()

if args.deprogram:
    dhost.deprogram()
    something_happened = True
    print 'Deprogrammed %s.' % dhost.host

if args.resync:
    print 'Reset digitiser timer and sync timer'
    dhost.data_resync()
    something_happened = True

if args.start:
    # start tx
    print 'Starting TX on %s' % dhost.host,
    sys.stdout.flush()
    dhost.enable_data_output(enabled=True)
    dhost.registers.control.write(gbe_txen=True)
    print 'done.'
    sys.stdout.flush()
    something_happened = True

if args.stop:
    dhost.enable_data_output(enabled=False)
    print 'Stopped transmission on %s.' % dhost.host
    something_happened = True

if args.pulse:
    dhost.pulse_data_output(args.pulse_packets)
    print 'Pulsed {} packets per polarisation'.format(args.pulse_packets)
    something_happened = True

if args.ipython:
    import IPython
    IPython.embed()
    something_happened = True

if not something_happened:
    parser.print_help()

#dhost.disconnect()