# author: plasmashadow

import six
from random import choice, randint
from .exeception import TrackerException, \
    TrackerRequestException, TrackerResponseException
from six.moves.urllib.parse import urlparse
from collections import defaultdict, OrderedDict
import hashlib
import socket
import time
import struct

DEFAULT_CONNECTION_ID = 0x41727101980

__VESION__ = '0.0.5'

EVENT_DICT = {
    "started": 2,
    "none": 0,
    "completed": 1,
    "stopped": 3
}

CONNECT = 0
ANNOUNCE = 1
SCRAP = 2
ERROR = 3


def generation_randomid(size, integer=False):
    """generates random id for a given size"""
    digits = range(10)
    id = []
    for i in range(size):
        id.append(choice(digits))
    res = ''.join(map(str, id))
    if not integer:
        return res
    else:
        return int(res)


def _generate_peer_id():
    """http://www.bittorrent.org/beps/bep_0020.html"""
    peer_id = '-PU' + __VESION__.replace('.', '-') + '-'
    remaining = 20 - len(peer_id)
    numbers = [str(randint(0, 9)) for _ in xrange(remaining)]
    peer_id += ''.join(numbers)
    assert(len(peer_id) == 20)
    return peer_id

def _parseurl(url):
    """parses the udp trackert url"""
    parsed = urlparse(url)
    return parsed.hostname, parsed.port

def trim_hash(info_hash):
    """cleans up info hash"""
    if len(info_hash) == 40:
        return info_hash.decode("hex")
    if len(info_hash) != 20:
        raise TrackerRequestException("Infohash not equal to 20 digits", info_hash)
    return info_hash

class UDPTracker(object):

    """
      A Tracker for working with udp based
      tracking protocol

      Specifications are take from
      http://bittorrent.org/beps/bep_0015.html
      http://www.rasterbar.com/products/libtorrent/udp_tracker_protocol.html
    """

    __fields = [
        "info_hash",
        "peer_id",
        "downloaded",
        "left",
        "uploaded",
        "event",
        "ip_address",
        "key",
        "num_want",
        "port"
    ]

    def __init__(self, announce_url, timeout=2, **kwargs):

        self.host, self.port = _parseurl(announce_url)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.peer_id = _generate_peer_id()
        self._connection_id = DEFAULT_CONNECTION_ID
        self._transaction = {}
        self.timeout = timeout
        self.info_hash = kwargs.get('info_hash')

    def build_header(self, action):
        transaction_id = randint(0, 1 << 32 -1)
        return transaction_id, struct.pack('!QLL', self._connection_id, action, transaction_id)

    def send(self, action, payload=None):
        if not payload:
            payload = ''
        trans_id, header = self.build_header(action)
        self._transaction[trans_id] = trans = {
            'action': action,
            'time': time.time(),
            'payload': payload,
            'completed': False,
        }
        self.sock.sendto(header + payload, (self.host, self.port))
        return trans

    def connect(self):
        return self.send(CONNECT)

    def announce(self, **kwargs):

        if not kwargs:
            raise TrackerRequestException("Argument Missing for ", self.announce.__name__)

        arguments = dict.fromkeys(self.__fields)
        arguments['info_hash'] = trim_hash(self.info_hash)
        arguments['port'] = 6800
        arguments['numwant'] = 10
        arguments.update(kwargs)

        values = [arguments[a] for a in self.__fields]
        payload = struct.pack('!20s20sQQQLLLLH', *values)
        return self.send(ANNOUNCE, payload=payload)

    def scrape(self, hashes):

        if len(hashes) > 74:
            raise TrackerRequestException('Max of 74 Request can be scraped', hashes)

        payload = ''
        for hash in hashes:
            hash = trim_hash(hash)
            payload += hash

        trans = self.send(SCRAP, payload)
        trans['sent_hashes'] = hashes
        return trans

    def interpret(self):

        self.sock.settimeout(timeout=self.timeout)

        try:
            response = self.sock.recv(10240)
        except socket.timeout:
            return dict()

        headers = response[:8]
        payload = response[8:]

        action, trans_id = struct.unpack('!LL', headers)

        try:
            trans = self._transaction[trans_id]
        except KeyError:
            raise TrackerResponseException("InvalidTransaction: id not found", trans_id)

        trans['response'] = self._process(action, payload, trans)
        trans['completed'] = True
        del self._transaction[trans_id]
        return trans

    def _process(self, action, payload, trans):

        if action == CONNECT:
            return self._process_connect(payload, trans)
        elif action == ANNOUNCE:
            return self._process_announce(payload, trans)
        elif action == SCRAP:
            return self._process_scrape(payload, trans)
        elif action == ERROR:
            return self._process_error(payload, trans)

        else:
            raise TrackerResponseException("Invalid Action", action)

    def _process_connect(self, payload, trans):

        self._connection_id = struct.unpack('!Q', payload)[0]
        return self._connection_id

    def _process_error(self, payload, trans):

        message = struct.unpack("!8s", payload)
        raise TrackerResponseException("Error Response", message)

    def _process_announce(self, payload, trans):

        response = {}

        info_struct = '!LLL'
        info_size = struct.calcsize(info_struct)
        info = payload[:info_size]
        interval, leechers, seeders = struct.unpack(info_struct, info)

        peer_data = payload[info_size:]
        peer_struct = '!LH'
        peer_size = struct.calcsize(peer_struct)
        peer_count = len(peer_data) / peer_size
        peers = []

        for peer_offset in xrange(peer_count):
            off = peer_size * peer_offset
            peer = peer_data[off:off + peer_size]
            addr, port = struct.unpack(peer_struct, peer)
            peers.append({
                'addr': socket.inet_ntoa(struct.pack('!L', addr)),
                'port': port,
            })

        return dict(interval=interval,
                    leechers=leechers,
                    seeders=seeders,
                    peers=peers)

    def _process_scrape(self, payload, trans):

        info_struct = '!LLL'
        info_size = struct.calcsize(info_struct)
        info_count = len(payload) / info_size
        hashes = trans['sent_hashes']
        response = {}
        for info_offset in xrange(info_count):
            off = info_size * info_offset
            info = payload[off:off + info_size]
            seeders, completed, leechers = struct.unpack(info_struct, info)
            response[hashes[info_offset]] = {
                'seeders': seeders,
                'completed': completed,
                'leechers': leechers,
            }

        return response

