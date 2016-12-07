#!/usr/bin/env python 
from mpd import MPDClient
client = MPDClient()               # create client object
client.timeout = 10                # network timeout in seconds (floats allowed), default: None
client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default:$
client.connect("localhost", 6600)  # connect to localhost:6600
currentsong = client.currentsong()
print ""
print 'CURRENT----------------------------------------------------------------'
if len(currentsong) > 0:
   for text in currentsong:
      print text + ": " + str(currentsong.get(text))
   current_id = int(currentsong.get("pos")) + 1
else:
   print "No current song (empty playlist)"
print ""
print 'STATUS-----------------------------------------------------------------'
status = client.status()
for text in status:
   print text + ": " + str(status.get(text))
print ""
print 'STATS------------------------------------------------------------------'
stats = client.stats()
for text in stats:
   print text + ": " + str(stats.get(text))
client.close()                     # send the close command
client.disconnect()                # disconnect from the server