# PuxHelper
Performs various tasks and uses PushBullet to communicate with the user.

Requires:
Transmission (BitTorrent client)
Transmissionrpc (Python module)
requests (Python module)
PushBullet account (Put authentication key in a text file somewhere then change PuxGlobal so my thing can find it)
NoPubWebAdapters that given a search dictionary {'URL': show_url} will return a list of tuples (episode number,torrent url)
