import unittest

from bencode import bdecode
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
    value = '-'+client_id+client_version+'-'+random_string
    assert len(value) == 20
    return value


class TestUDPTracker(unittest.TestCase):
    """
      Test Class for testing the udp tracker protocol
    """

    def setUp(self):
        content = open('sample.torrent', 'rb').read()
        self.content = bdecode(content)
        self.connection_id = None
        self.transaction_id = None
        self.announc_url = self.content.get('announce')
        log.info(self.content)

    def test_connect(self):
        """test whether it is connecting or not"""
        tracker = UDPTracker(self.announc_url, timeout=5)