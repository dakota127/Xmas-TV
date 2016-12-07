#!/usr/bin/env python 
from mpd import MPDClient
import sys

global TEST_MPD_HOST, TEST_MPD_PORT, TEST_MPD_PASSWORD
TEST_MPD_HOST     = "localhost"
TEST_MPD_PORT     = "6600"
TEST_MPD_PASSWORD = "volumio"   # password for Volumio / MPD


#-----------------------------------------------
def connect_mpd():
# Connect with MPD
#------------------------------------------------
    connected = False
    retry_count=3
    i=1
    while connected == False:
        connected = True
        try:
             client.connect(TEST_MPD_HOST, TEST_MPD_PORT)
        except SocketError as e:
             connected = False
        if connected == False:
                print "Couldn't connect. Retrying"
                i=i+1
                if i > retry_count:
                    return(9)
                time.sleep(3)
    print("Connected to MPD-Server")
    return(0)


#--------------------------------------
#---- Main ------------------


client = MPDClient()               # create client object
client.timeout = 10                # network timeout in seconds (floats allowed), default: None
client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default:$
ret=connect_mpd()                    # connect to localhost:6600
if ret==9:
    print "Could not connect to MPD"
    sys.exit(2)

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
   
   
print 'Volume-----------------------------------------------------------------'
status = client.status()
for text in status:
    if text=="volume":
        print text + ": " + str(status.get(text))
print ""
   
   
client.close()                     # send the close command
client.disconnect()                # disconnect from the server