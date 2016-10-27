import logging
import spead2
import spead2.send
import struct
import socket

from casperfpga.tengbe import IpAddress

from fxcorrelator_speadops import SPEAD_ADDRSIZE

LOGGER = logging.getLogger(__name__)

DIGITISER_ADC_SAMPLES = 0
FENGINE_CHANNELISED_DATA = 1
XENGINE_CROSS_PRODUCTS = 2
BEAMFORMER_FREQUENCY_DOMAIN = 3
BEAMFORMER_TIME_DOMAIN = 4

SPEAD_PKT_TTL = 2


class StreamAddress(object):
    """
    A data source from an IP. Holds all the information we need to use
    that data source.
    """
    def __init__(self, ip_string, ip_range, port):
        """

        :param ip_string: the ip address at which it can be found - a dotted
        decimal STRING
        :param ip_range: the consecutive number of IPs over which it is spread
        :param port: the port to which it is sent
        :return:
        """
        self.ip_address = IpAddress(ip_string)
        self.ip_range = ip_range
        self.port = port

    @staticmethod
    def _parse_address_string(address_string):
        """

        :param address_string:
        :return:
        """
        try:
            _bits = address_string.split(':')
            port = int(_bits[1])
            if '+' in _bits[0]:
                address, number = _bits[0].split('+')
                number = int(number) + 1
            else:
                address = _bits[0]
                number = 1
            assert(len(address.split('.')) == 4)
        except ValueError:
            raise RuntimeError('The address %s is not correctly formed. Expect '
                               '1.2.3.4+50:7777. Bailing.', address_string)
        return address, number, port

    @classmethod
    def from_address_string(cls, address_string):
        """
        Parse a 1.2.3.4+50:7777 string and return a StreamAddress
        :param address_string:
        :return:
        """
        address, number, port = StreamAddress._parse_address_string(
            address_string)
        return cls(address, number, port)

    def is_multicast(self):
        """
        Does the data source's IP address begin with 239?
        :return:
        """
        return self.ip_address.is_multicast()

    def __eq__(self, other):
        """
        Override the default Equals behavior
        """
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        """
        Define a non-equality test
        """
        if isinstance(other, self.__class__):
            return not self.__eq__(other)
        return NotImplemented

    def __repr__(self):
        return '%s+%i:%i' % (self.ip_address, self.ip_range-1, self.port)

    def __str__(self):
        return '%s+%i:%i' % (self.ip_address, self.ip_range-1, self.port)


# class DataStream(object):
#     """
#     A data stream produced by some instrument function. A name, a category,
#     a StreamAddress for data and one for metadata. Some callbacks to do things
#     when these addresses change.
#     """
#     def __init__(self,
#                  name,
#                  category,
#                  destination,
#                  tx_enable_method=None,
#                  tx_disable_method=None,
#                  destination_cb=None):
#         """
#         :param name: the name of this data stream
#         :param destination: a StreamAddress for the stream data destination
#         :param tx_enable_method: method to call to start transmission of this
#         stream
#         :param tx_disable_method: method to call to stop transmission of this
#         stream
#         :param destination_cb: a callback to run when this data stream
#         destination is updated
#         :return:
#         """
#         self.name = name
#         self.category = category
#         # tx enable and disable methods
#         self.tx_enable_callback = tx_enable_method
#         self.tx_disable_callback = tx_disable_method
#         # destination
#         self.destination = destination
#         self.destination_cb = destination_cb
#
#     def set_destination(self, new_address):
#         """
#         Change the destination for this data stream
#         :param new_address: a StreamAddress
#         :return:
#         """
#         if self.destination == new_address:
#             LOGGER.info('%s: destination already %s' %
#                         (self.name, self.destination))
#             return
#         self.destination = new_address
#         if self.destination_cb:
#             self.destination_cb(self)
#         LOGGER.info('%s: set destination to %s' %
#                     (self.name, self.destination))
#
#     def tx_enable(self):
#         """
#         Enable TX for this data stream
#         :return:
#         """
#         if self.tx_enable_callback:
#             self.tx_enable_callback(self)
#             LOGGER.info('DataStream %s - output enabled' % self.name)
#         else:
#             LOGGER.warn('DataStream %s does not support tx_enable' % self.name)
#
#     def tx_disable(self):
#         """
#         Disable TX for this data stream
#         :return:
#         """
#         if self.tx_disable_callback:
#             self.tx_disable_callback(self)
#             LOGGER.info('DataStream %s - output disabled' % self.name)
#         else:
#             LOGGER.warn('DataStream %s does not support tx_disable' % self.name)
#
#     def __repr__(self):
#         return self.__str__()
#
#     def __str__(self):
#         return 'DataStream(%s:%i), data(%s)' % (
#             self.name, self.category, self.destination)
#
#
# def _setup_spead(meta_address):
#     """
#     Set up a SPEAD ItemGroup and transmitter.
#     :param meta_address: where are messages on this socket sent?
#     :return:
#     """
#     flavour = spead2.Flavour(4, 64, SPEAD_ADDRSIZE)
#     meta_ig = spead2.send.ItemGroup(flavour=flavour)
#     streamconfig = spead2.send.StreamConfig(max_packet_size=4096, max_heaps=8)
#     streamsocket = socket.socket(
#         family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_IP)
#     ttl_bin = struct.pack('@i', SPEAD_PKT_TTL)
#     streamsocket.setsockopt(
#         socket.IPPROTO_IP,
#         socket.IP_MULTICAST_TTL,
#         ttl_bin)
#     meta_tx = spead2.send.UdpStream(
#         spead2.ThreadPool(), str(meta_address.ip_address), meta_address.port,
#         streamconfig, 5120000, streamsocket)
#     return meta_ig, meta_tx
#
#
# class DataMetaStream(DataStream):
#     """
#     A DataStream that also has metadata stream internally.
#     """
#     def __init__(self, name, category,
#                  destination,
#                  tx_enable_method=None,
#                  tx_disable_method=None,
#                  destination_cb=None):
#         """
#         :param name: the name of this data stream
#         :param destination: a StreamAddress for the stream data destination
#         :param tx_enable_method: method to call to start transmission of this
#         stream
#         :param tx_disable_method: method to call to stop transmission of this
#         stream
#         :param destination_cb: a callback to run when this data stream
#         destination is updated
#         :return:
#         """
#         # metadata
#         self.meta_destination = None
#         self.meta_destination_cb = None
#         self.meta_ig = None
#         self.meta_tx = None
#         super(DataMetaStream, self).__init__(
#             name, category, destination, tx_enable_method, tx_disable_method,
#             destination_cb)
#
#     def set_meta_destination(self, new_address):
#         """
#         Change the meta destination for this data stream
#         :param new_address: a StreamAddress
#         :return:
#         """
#         if self.meta_destination == new_address:
#             LOGGER.info('%s: destination already %s' %
#                         (self.name, self.destination))
#             return
#         self.meta_destination = new_address
#         self.meta_ig, self.meta_tx = _setup_spead(self.meta_destination)
#         if self.meta_destination_cb:
#             self.meta_destination_cb(self)
#         LOGGER.info('%s: set meta destination to %s' %
#                     (self.name, self.destination))
#
#     def meta_issue(self):
#         """
#         Call the meta destination update callback, then transmit the metadata.
#         :return:
#         """
#         self.meta_destination_cb(self)
#         self.meta_transmit()
#
#     def meta_transmit(self):
#         """
#         Send the metadata for this data stream.
#         :return:
#         """
#         if self.meta_ig is None:
#             LOGGER.info('SPEAD meta itemgroup for data stream %s is '
#                         'unavailable, not sending metadata.' %
#                         self.name)
#             return
#         if self.meta_tx is None:
#             LOGGER.info('SPEAD meta transmitter for data stream %s is '
#                         'unavailable, not sending metadata.' %
#                         self.name)
#             return
#         heap = self.meta_ig.get_heap(descriptors='all', data='all')
#         self.meta_tx.send_heap(heap)
#         LOGGER.info('DataStream %s sent SPEAD metadata to %s' % (
#             self.name, self.meta_destination))
#
#     def tx_enable(self):
#         """
#         Enable TX for this data stream
#         :return:
#         """
#         try:
#             heapgen = spead2.send.HeapGenerator(self.meta_ig)
#             self.meta_tx.send_heap(heapgen.get_start())
#         except AttributeError:
#             LOGGER.warning('Installed version of SPEAD2 does not seem to'
#                            'support stream start packets?')
#         super(DataMetaStream, self).tx_enable()
#
#     def tx_disable(self):
#         """
#         Disable TX for this data stream
#         :return:
#         """
#         super(DataMetaStream, self).tx_disable()
#         try:
#             heapgen = spead2.send.HeapGenerator(self.meta_ig)
#             self.meta_tx.send_heap(heapgen.get_end())
#         except AttributeError:
#             LOGGER.warning('Installed version of SPEAD2 does not seem to'
#                            'support stream stop packets?')
#
#     def __str__(self):
#         return 'DataStreamMeta(%s:%i), data(%s) meta(%s)' % (
#             self.name, self.category, self.destination, self.meta_destination)


def _setup_spead_tx(ip_string, port):
    """
    Set up a SPEAD transmitter.
    :param ip_string: where are messages on this socket sent?
    :param port: and on which port?
    :return:
    """
    streamconfig = spead2.send.StreamConfig(max_packet_size=4096, max_heaps=8)
    streamsocket = socket.socket(
        family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_IP)
    ttl_bin = struct.pack('@i', SPEAD_PKT_TTL)
    streamsocket.setsockopt(
        socket.IPPROTO_IP,
        socket.IP_MULTICAST_TTL,
        ttl_bin)
    tx = spead2.send.UdpStream(
        spead2.ThreadPool(), ip_string, port,
        streamconfig, 64 * 1024, streamsocket)
    return tx


class SPEADStream(object):
    """
    A DataStream that is also a SPEAD stream.
    Sends SPEAD data descriptors on tx_enable.
    """
    def __init__(self, name, category, destination):
        """
        Make a SPEAD stream.
        :param name: the name of the stream
        :param category: what kind of stream is this
        :param destination: where is it going?
        :return:
        """
        self.name = name
        self.category = category
        self.destination = None
        self.descr_tx = None
        self.descr_ig = spead2.send.ItemGroup(
            flavour=spead2.Flavour(4, 64, SPEAD_ADDRSIZE))
        self.descriptors_setup()
        self.set_destination(destination)

    def descriptors_setup(self):
        """
        Set up the item descriptors for this stream. This must be implemented
        by the subclass.
        :return:
        """
        raise NotImplementedError

    def set_destination(self, new_dest):
        """
        Set the destination for this stream
        :param new_dest: the new destination to use
        :return:
        """
        if new_dest is None:
            LOGGER.warning('%s: stream destination not set' % self.name)
            return
        if not hasattr(new_dest, 'ip_address'):
            new_dest = StreamAddress.from_address_string(new_dest)
        self.destination = new_dest
        # make the SPEAD transmitters, one for every address
        self.descr_tx = []
        for dest_ctr in range(self.destination.ip_range):
            ip = IpAddress.ip2str(int(self.destination.ip_address) + dest_ctr)
            LOGGER.info('Making speadtx for stream %s: %s:%d' % (
                self.name, str(ip), self.destination.port))
            tx = _setup_spead_tx(ip, self.destination.port)
            self.descr_tx.append(tx)

    def descriptors_issue(self):
        """
        Issue the data descriptors for this data stream
        :return:
        """
        if (not self.descr_ig) or (not self.descr_tx):
            LOGGER.info('%s: descriptors have not been set up for '
                        'stream yet.' % self.name)
            return
        ctr = 0
        for tx in self.descr_tx:
            tx.send_heap(self.descr_ig.get_heap(descriptors='all', data='all'))
            ctr += 1
        LOGGER.info('SPEADStream %s: sent descriptors to %d destination%s' % (
            self.name, ctr, '' if ctr == 1 else 's'))

    def tx_enable(self):
        """
        Enable TX for this data stream
        :return:
        """
        # when implementing this, you should issue descriptors
        # before enabling the hardware.
        raise NotImplementedError

    def tx_disable(self):
        """
        Disable TX for this data stream
        :return:
        """
        raise NotImplementedError

    def __str__(self):
        return 'SPEADStream %s:%i -> %s' % (
            self.name, self.category, self.destination)


class SPEADStreamMeta(SPEADStream):
    """
    A SPEADStream with metadata sent as well.
    """
    def __init__(self, name, category, destination):
        self.meta_ig = spead2.send.ItemGroup(
            flavour=spead2.Flavour(4, 64, SPEAD_ADDRSIZE))
        super(SPEADStreamMeta, self).__init__(name, category, destination)

    def metadata_setup(self):
        """
        Add relevant metadata to the ItemGroup
        :return:
        """
        raise NotImplementedError

    def metadata_issue(self):
        """
        Send SPEAD metadata related to this stream.
        :return:
        """
        if (not self.meta_ig) or (not self.descr_tx):
            LOGGER.info('%s: metadata has not been set up for '
                        'stream yet.' % self.name)
            return
        ctr = 0
        for tx in self.descr_tx:
            tx.send_heap(self.meta_ig.get_heap(descriptors='all', data='all'))
            ctr += 1
        LOGGER.info('SPEADStream %s: sent metadata to %d destination%s' % (
            self.name, ctr, '' if ctr == 1 else 's'))