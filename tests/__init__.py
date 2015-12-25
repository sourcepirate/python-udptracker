import unittest

from bencode import bdecode
from udptrack import UDPTracker
from udptrack import DEFAULT_CONNECTION_ID
from udptrack.exeception import *
import udptrack
import logging
import mock

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

    @mock.patch.object(UDPTracker, 'send')
    def test_connect(self, mock_send):
        """test whether the connect function is behaving
           properly.
        """
        tracker = UDPTracker(self.announc_url, timeout=5)
        tracker.connect()
        mock_send.assert_called_with(udptrack.CONNECT)

    @mock.patch('udptrack.trim_hash')
    @mock.patch.object(UDPTracker, 'send')
    @mock.patch.object(udptrack.struct, 'pack')
    def test_announce(self, mock_pack, mock_send, mock_trim):
        """test whether the announce function is working
        properly
        """
        tracker = UDPTracker(self.announc_url, timeout=5)
        tracker.announce(info_hash=None)
        mock_trim.assert_called_with(None)
        args, kwargs = mock_send.call_args
        self.assertEqual(args, (udptrack.ANNOUNCE,))
        self.assertTrue(mock_pack.called)

    @mock.patch('udptrack.trim_hash')
    @mock.patch.object(UDPTracker, 'send')
    @mock.patch.object(udptrack.struct, 'pack')
    def test_scrap(self, mock_pack, mock_send, mock_trim):
        """test whether the announce function is working
        properly
        """
        tracker = UDPTracker(self.announc_url, timeout=5)
        tracker.scrape(["hash"])
        mock_trim.assert_called_with('hash')
        args, kwargs = mock_send.call_args
        self.assertEqual(args, (udptrack.SCRAP,))
        self.assertRaises(TrackerRequestException)