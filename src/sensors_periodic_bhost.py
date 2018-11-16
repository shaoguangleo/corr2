import logging
import tornado.gen as gen
from tornado.ioloop import IOLoop

import sys
import traceback as tb

from casperfpga.transport_katcp import KatcpRequestError, KatcpRequestFail, \
    KatcpRequestInvalid

from sensors import Corr2Sensor, boolean_sensor_do

LOGGER = logging.getLogger(__name__)

host_offset_lookup = {}
sensor_poll_time = 10


@gen.coroutine
def _cb_bhost_lru(sensor_manager, sensor, b_host):
    """
    Sensor call back function for x-engine LRU
    :param sensor:
    :return:
    """
    #TODO - just copied from _cb_xhost_lru function, need to update.
    # try:
    #     h = host_offset_lookup[b_host.host]
    #     # Pdb().set_trace()
    #     status = Corr2Sensor.NOMINAL
    #     for xctr in range(b_host.x_per_fpga):
    #         pref = '{bhost}.beng{xctr}'.format(bhost=h, xctr=xctr)
    #         eng_status = Corr2Sensor.NOMINAL
    #         if sensor_manager.sensor_get(
    #                 "{}.vacc.device-status".format(pref)).status() == Corr2Sensor.ERROR:
    #             status = Corr2Sensor.ERROR
    #             eng_status = Corr2Sensor.ERROR
    #         elif sensor_manager.sensor_get("{}.bram-reorder.device-status".format(pref)).status() == Corr2Sensor.ERROR:
    #             status = Corr2Sensor.ERROR
    #             eng_status = Corr2Sensor.ERROR
    #         sens_val = (eng_status == Corr2Sensor.NOMINAL)
    #         sensor_manager.sensor_get(
    #             "{}.device-status".format(pref)).set(value=sens_val, status=eng_status)
    #
    #     if sensor_manager.sensor_get(
    #             "{}.network.device-status".format(h)).status() == Corr2Sensor.ERROR:
    #         status = Corr2Sensor.ERROR
    #     elif sensor_manager.sensor_get("{}.network-reorder.device-status".format(h)).status() == Corr2Sensor.ERROR:
    #         status = Corr2Sensor.ERROR
    #     elif sensor_manager.sensor_get("{}.network.device-status".format(h)).status() == Corr2Sensor.WARN:
    #         status = Corr2Sensor.WARN
    #     elif sensor_manager.sensor_get("{}.network-reorder.device-status".format(h)).status() == Corr2Sensor.WARN:
    #         status = Corr2Sensor.WARN
    #     sens_val = (status == Corr2Sensor.NOMINAL)
    #     sensor.set(value=sens_val, status=status)
    # except Exception as e:
    #     LOGGER.error(
    #         'Error updating LRU sensor for {} - {}'.format(
    #             b_host.host, e.message))
    #     sensor.set(value=False, status=Corr2Sensor.FAILURE)
    #
    # LOGGER.debug('_cb_xhost_lru ran on {}'.format(b_host.host))
    # IOLoop.current().call_later(
    #     sensor_poll_time,
    #     _cb_xhost_lru,
    #     sensor_manager,
    #     sensor,
    #     b_host)


@gen.coroutine
def _cb_beng_pack(sensors, general_executor, sens_man):
    """

    :param sensors: all sensors for all bengine pack blocks, a list of dictionaries.
    :return:
    """
    value = True
    status = Corr2Sensor.NOMINAL

    try:

        executor = general_executor
        #rv = yield executor.submit(sens_man.instrument.bops.get_pack_status) # Skip this.
        rv = []
        for beam_no in xrange(len(sens_man.instrument.bops.beams)):
            beam_sensors = []
            for bhost in sens_man.instrument.xhosts:
                beam_sensors.append(bhost.get_bpack_status(beam_no))
            rv.append((beam_sensors))

        for beam_no, beam_sensors in enumerate(sensors):
            for bhost_no, bhost_sensors in enumerate(beam_sensors):
                for beng_no, beng_sensors in enumerate(bhost_sensors):
                    for key in ['fifo_of_err_cnt', 'pkt_cnt']:
                        print "Trying to set {} value to: {}".format(key, rv[beam_no][bhost_no][beng_no])
                        beng_sensors[key].set(value=rv[beam_no][bhost_no][beng_no], errif='changed')
                        #print bhost_sensors[key]
                        if beng_sensors[key].status() == Corr2Sensor.ERROR:
                            status = Corr2Sensor.ERROR
                            value = False
                    beng_sensors['device_status'].set(value=value, status=status)

                    print "\n\nObject representation: {}\n\n\n\n".format(beng_sensors)

    except Exception as e:
        print "{}".format(tb.format_exception(*sys.exc_info()))
        import IPython; IPython.embed()

        #LOGGER.error('Error updating beng pack sensors for {} - '
                     #'{}'.format(b_host.host, e.message))
    #LOGGER.debug('_cb_beng_pack ran on {}'.format(b_host.host))
    IOLoop.current().call_later(sensor_poll_time, _cb_beng_pack, sensors, general_executor, sens_man)


def setup_sensors_bengine(sens_man, general_executor, host_executors, ioloop,
                          host_offset_dict):
    """
    Set up the B-engine specific sensors.
    :param sens_man:
    :param general_executor:
    :param host_executors:
    :param ioloop:
    :param host_offset_dict:
    :return:
    """
    global host_offset_lookup
    global sensor_poll_time
    sensor_poll_time = sens_man.instrument.sensor_poll_time
    if len(host_offset_lookup) == 0:
        host_offset_lookup = host_offset_dict.copy()

    # Beng Packetiser block
    beam_sensors = []
    for beamctr in range(len(sens_man.instrument.bops.beams)):
        bhost_sensors = []
        for _b in sens_man.instrument.xhosts:
            executor = general_executor
            bhost = host_offset_lookup[_b.host]
            beng_sensors = []
            for bengctr in range(_b.x_per_fpga):  # TODO alias this to b_per_fpga for consistency
                pref = 'beam{beamctr}.{bhost}.beng{bengctr}.spead-tx'.format(beamctr=beamctr, bhost=bhost, bengctr=bengctr)
                sensordict = {
                    'device_status': sens_man.do_sensor(
                        Corr2Sensor.boolean,
                        '{}.device-status'.format(pref),
                        'B-engine pack (TX) status',
                        executor=executor),
                    'fifo_of_err_cnt': sens_man.do_sensor(
                        Corr2Sensor.integer,
                        '{}.fifo-of-err-cnt'.format(pref),
                        'B-engine pack (TX) FIFO overflow error count',
                        executor=executor),
                    'pkt_cnt': sens_man.do_sensor(
                        Corr2Sensor.integer,
                        '{}.pkt-cnt'.format(pref),
                        'B-engine pack (TX) packet count',
                        executor=executor)}
                beng_sensors.append(sensordict)
            bhost_sensors.append(beng_sensors)
        beam_sensors.append(bhost_sensors)
    ioloop.add_callback(_cb_beng_pack, beam_sensors, general_executor, sens_man)

    # LRU ok
    sensor = sens_man.do_sensor(
        Corr2Sensor.boolean, '{}.device-status'.format(bhost),
        'B-engine %s LRU ok' % _b.host, executor=executor)
    #TODO think a little bit more about how this needs to work.
    # for bengctr in range(_b.x_per_fpga):
    #     pref = '{bhost}.beng{bengctr}'.format(bhost=bhost, bengctr=bengctr)
    #     sens_man.do_sensor(
    #         Corr2Sensor.boolean,
    #         '{}.device-status'.format(pref),
    #         'B-engine core status')
    ioloop.add_callback(_cb_bhost_lru, sens_man, sensor, _b)

    # TODO - right now this just mirrors the xhostn-lru-ok sensors

#    # B-engine host sensors
#    for _x in sens_man.instrument.xhosts:
#        executor = host_executors[_x.host]
#        xhost = host_offset_lookup[_x.host]
#        bhost = xhost.replace('xhost', 'bhost')
#
#        # LRU ok
#        sensor = sens_man.do_sensor(
#            Corr2Sensor.boolean, '{}-lru-ok'.format(bhost),
#            'B-engine %s LRU ok' % _x.host, executor=executor)
#        ioloop.add_callback(_cb_beng_lru, sensor, _x)
#
#    #BENG packetiser
#    for _x in sens_man.instrument.xhosts:
#        executor = host_executors[_x.host]
#        xhost = host_offset_lookup[_x.host]
#        # beng
#        sensors = []
#        for xctr in range(_x.x_per_fpga):
#            bsensors = []
#            for pctr in range(2):
#                sensor_name = '{host}-beng{x}-{p}.device-status'.format(
#                    host=xhost, x=xctr, p=pctr)
#                sensor_descrip = '{host} b-engine{x}-{p} ok'.format(
#                    host=xhost, x=xctr, p=pctr)
#                sensor = sens_man.do_sensor(Corr2Sensor.boolean, sensor_name,
#                                            sensor_descrip, executor=executor)
#                bsensors.append(sensor)
#            sensors.append(bsensors)
#        ioloop.add_callback(_cb_beng_pack, sensors, _x)
