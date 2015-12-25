##UDPTRACK

A Bittorrent udp-tracking protocol Based on the specifications given by
http://www.rasterbar.com/products/libtorrent/udp_tracker_protocol.html

##Installation

```
 pip install python-udptrack

```

##Usage

In order to connect to the tracker the tracker url and info_hash is necessary.

<b>Note</b>: I assume that you have already decoded torrent file dict.

```python

from udptrack import UDPTracker

announce_url = torrent_info_dict.get("announce")

tracker = UDPTracker(announce_url, timeout=2, info_hash="7BC238FD69F5A43C1CD5566870420D63F074BAD8")
tracker.connect()
print tracker.interpret()

```

In order to announce you can have announce method.

```python

tracker.announce()
print tracker.interpret()

```

In order to scrap the details of torrent

```python

tracker.scrape(["7BC238FD69F5A43C1CD5566870420D63F074BAD8"])
print tracker.interpret()

```


###License
<b> BSD </b>