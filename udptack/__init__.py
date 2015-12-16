#author: plasmashadow

import six
from random import choice, sample
from json import dumps, loads
from .exeception import TrackerException, \
    TrackerRequestException, TrackerResponseException
from bencode import Bencoder
from six.moves.urllib.parse import urlparse
from collections import defaultdict
import hashlib, socket
import struct

DEFAULT_CONNECTION_ID = 0x41727101980

EVENT_DICT = {
    "started": 2,
    "none": 0,
    "completed": 1,
    "stopped": 3
}

CONNECT_ACTION = 0
ANNOUNCE_ACTION = 1
SCRAP_ACTION = 2


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


class UDPTracker(object):

    """
      A Tracker for working with udp based
      tracking protocol

      Specifications are take from
      http://bittorrent.org/beps/bep_0015.html
      http://www.rasterbar.com/products/libtorrent/udp_tracker_protocol.html
    """

    def __init__(self, metadata, peer_id, **kwargs):

        self._connection_id = DEFAULT_CONNECTION_ID
        self._trans_id = generation_randomid(5, integer=True)
        parsed = loads(metadata)
        self._tracker_url = parsed.get("announce", None)
        if not self._tracker_url:
            raise TrackerException("No announce URL present", parsed)
        self.id = peer_id
        self.info = parsed.get("info")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._misc = kwargs
        self._downloaded = 0
        self._uploaded = 0

    @property
    def info_hash(self):
        """info hash holds the hashed value of info object"""
        encoded = Bencoder.encode(self.info)
        return hashlib.sha1(encoded).digest()

    @property
    def url(self):
        url_d = urlparse(self._tracker_url)
        return url_d.host, url_d.port

    @property
    def left(self):
        return 0

    def _gen_connect(self):
        """generates the connect packet for udp tracker"""
        return struct.pack(">qii", self._connection_id, CONNECT_ACTION, self._trans_id)

    def _get_announce(self, event="none"):
        """generates announce packet to the tracker"""

        packet = struct.Struct(">qii20s20sqqqiiiih")
        event = EVENT_DICT.get(event, EVENT_DICT["none"])

        packet_data = packet.pack(self._connection_id, ANNOUNCE_ACTION, self._trans_id,
                                  self.info_hash, self.id, self._downloaded, self.left, self._uploaded,
                                  event, self._misc.get("ip", 0), generation_randomid(4, integer=True),
                                  -1, self._misc.get("port", 6060))

        return packet_data

    def _get_scrape(self, info_hashes):
        """generates the packets for scrape request"""

        _struct = "qii"
        _struct += "20s" * len(info_hashes)
        _list = [self._connection_id, SCRAP_ACTION, self._trans_id]
        _list.extend(info_hashes)
        packet = struct.Struct(_struct)
        return packet.pack(*_list)

    def _sendto(self, address, message):
        """sends the message to specific address"""
        self.sock.sendto(message, address)
        response = self.sock.recvfrom(1024)
        return self._parse(response)

    def _parse(self, response):
        """parse the response based on action"""
        data, address = response
        response = defaultdict(lambda x: None)
        act = struct.unpack(">i", data[:4])
        act = act[0]

        if act == 3:
            tid, message = struct.unpack(">i8s", data[4:])
            raise TrackerRequestException(message=message, data="")

        elif act == 0:
            tid, cid = struct.unpack(">iq", data[4:])
            response['transaction_id'] = tid
            response['connection_id'] = cid
            return act, response

        elif act == 1 and len(data) >= 20:
            transaction_id, interval, leechers, seeders =\
            struct.unpack("!LLLL", data[4:20])
            if transaction_id != self._trans_id:
                raise TrackerException(message="invalid transaction id", data=transaction_id)
            response['action'] = act
            response['transaction_id'] = transaction_id
            response['interval'] = interval
            response['leechers'] = leechers
            response['seeders'] = seeders
            peers = []
            more_data = data[20:]
            while True:
                try:
                    ip_port = struct.Struct("!ih")
                    size = ip_port.size
                    ip, port = ip_port.unpack(more_data[:size])
                    more_data = more_data[size:]
                    ip = socket.inet_ntoa(struct.pack('!L', ip))
                    peers.append((ip, port))
                except:
                    break
            response['peers'] = peers
            return act, response

        elif act == 2:
            action, transaction_id = struct.unpack("!LL", data)
            if transaction_id == self._trans_id:
                raise TrackerException(message="invalid transaction id", date=transaction_id)
            response['action'] = act
            response['transaction_id'] = transaction_id
            response['completed'] = []
            response['downloaded'] = []
            response['incomplete'] = []
            more_data = data[8:]
            while True:
                try:
                    raw_data = struct.Struct("!iii")
                    size = raw_data.size
                    completed, downloaded, incomplete = raw_data.unpack(more_data[:size])
                    more_data = more_data[size:]
                    response['completed'].append(completed)
                    response["downloaded"].append(downloaded)
                    response["incomplete"].append(incomplete)
                except:
                    break
            return act, response
        else:
            raise TrackerException(message="invalid response", data=data)

    def connect(self):
        """send a connect request to tracker"""
        act, response = self._sendto(self.url, self._gen_connect())
        self._connection_id = response.get("connection_id", DEFAULT_CONNECTION_ID)
        self._trans_id = response.get("transaction_id", self._trans_id)

    def announce(self):
        """sending an announce request to the trackers"""
        act, response = self._sendto(self.url, self._get_announce())
        pass