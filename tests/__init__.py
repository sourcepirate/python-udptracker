import unittest

from bencode import Bencoder
from udptrack import UDPTracker
import udptrack
import logging

import StringIO

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def _generate_pear_id(client_id, client_version):
    """generate a 20 char peer id"""
    from random import choice
    random_string = ""
    while len(random_string) != 12:
        random_string = random_string + choice("1234567890")
    return '-'+client_id+client_version+'-'+random_string


class TestUDPTracker(unittest.TestCase):
    """
      Test Class for testing the udp tracker protocol
    """

    def setUp(self):
        content = open('sample.torrent', 'rb').read()
        self.content = Bencoder.decode(content)
        self.connection_id = None
        self.transaction_id = None
        log.info(self.content)

    def test_connect(self):

        tracker = UDPTracker(self.content, _generate_pear_id('KO', '0001'))
        self.transaction_id = tracker._trans_id
        buffer = StringIO.StringIO(tracker.info["pieces"])
        log.info(buffer.read())
        tracker.connect()
        self.assertEqual(tracker._trans_id, self.transaction_id)
        self.connection_id = tracker._connection_id
        self.assertNotEqual(tracker._connection_id, udptrack.DEFAULT_CONNECTION_ID)