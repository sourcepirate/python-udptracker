from udptrack import UDPTracker
from bencode import bencode, bdecode
import hashlib


path = '/home/plasmashadow/peerworld/udptack/tests/sample.torrent'
content = open(path, 'rb').read()
dct = bdecode(content)
announce_url = dct['announce']

info_hash = hashlib.sha1(bencode(dct['info'])).hexdigest().upper()

tracker = UDPTracker(announce_url, info_hash=info_hash, timeout=5)
tracker.connect()
print tracker.interpret()

tracker.announce(info_hash=info_hash)
print tracker.interpret()

tracker.scrape(['7BC238FD69F5A43C1CD5566870420D63F074BAD8'])
print tracker.interpret()

