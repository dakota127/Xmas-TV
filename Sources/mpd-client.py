#!/usr/bin/python
# coding: utf-8
#------------------------------------------------------
# Client for mpd-Server
#   Programm starts 8 Threads
#
#   waits für button click on four buttons - sets up three interrupt routines
#   GPIO assignment:
#   button 1 (GPIO8) :      jump to next title in playlist
#   button 2 (GPIO24) :     jump to previuos title in playlist
#   button 3  (GPI23) :     jump to first title in playlist
#   button 4  (GPIO15) :    set mpd player to random mode (toggle)
#   Switch on pot (GPIO14) for other uses, checked at start
#
#   Led1 blinks as long as program runs
#   Pressing any button blinks Led2 (red) twice for visual feedback
#   Successful connection to mpd Server also blinks Led2 twice
#   keyboard Interrupt is catched for testing purposes in Terminal, signals termination to all threads vi variable exitapp
#
#   script waits also for random seconds to play station ID, suspends currentplaylist
#   script also starts thread to read volume potentiometer and sets mpd volume accordingly
#   code to read pot via chip MCP3008 is taken from Adafruits learning unit
#   Analog Inputs for Raspberry Pi Using the MCP3008 (they call it bit banged). 
#   This script uses GPIO Pins 4/17/27/22  for CLK/DOUT/CS/CS
#
#   Script is started via /etc/rc.local
#
#   Pretty simple version found on the Volumio-Forum (nextbutton)
#   Extended and adapted by Peter K. Boxler, December 2014 
#-------------------------------------------------------

import RPi.GPIO as GPIO
import sys, getopt, os
import mpd
import time
import random
from threading import Thread
from math import floor

GPIO.setmode(GPIO.BCM)
buttonPinNext 	= 8
buttonPinPrev 	= 24
buttonPinStart 	= 23
buttonPinRandom = 15
potschalter =   14

led1=25                 # green led blinks as long as script runs
led2=7                  # red led blinks three times: acks button press
led3=9                  # green led on= random play on off= random play off

# GPIO Pins for bit banged AD Converter (from Adafruit example)
SPICLK = 4
SPIMISO = 17
SPIMOSI = 27
SPICS = 22



debug=0
FALSE=0
TRUE=1
exitapp = FALSE
sleep_ping=30
randomstate=0
waitstatid_factor_long=100
waitstatid_factor_short=15
waitstatid=0                        # wait time til next station ID play
potswitch=0                         # status of pot switch at start time, check at start

global TEST_MPD_HOST, TEST_MPD_PORT, TEST_MPD_PASSWORD
TEST_MPD_HOST     = "localhost"
TEST_MPD_PORT     = "6600"
TEST_MPD_PASSWORD = "volumio"   # password for Volumio / MPD


# ***** Function Parse commandline arguments ***********************
# get and parse commandline args

def arguments(argv):
    global  debug
    try:
        opts, args=getopt.getopt(argv,"dh")
    except getopt.GetoptError:
        print ("Parameter Error")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print ("App mpd-client -----------------------------------")
            print ("usage: mpd-client [-s -h]")
            sys.exit(2)
        elif opt == '-d': 	debug = 1
	
# ***********************************************

#-----------------------------------------------------------  
# get next song to be played          
def get_nexid(mpd):
    global  debug

    status = mpd.status()
    for text in status:
            if text=="nextsongid":
                nexid=int(status.get(text))
                if debug: print "Next SongID: %d" % nexid 
    return(nexid)


#----------------------------------------------------------- 
# lower volume from current value to zero, returns current value           
def lower_volume(mpd):
    global  debug

    status = mpd.status()
    for text in status:
            if text=="volume":
                curvol=int(status.get(text))
                if debug: print "Current Volume: %d" % curvol 
    volume=curvol
    if debug: print "Decreasing Volume"
    while TRUE:
        volume=volume-10
        if volume<0: 
            volume=0
            mpd.setvol(volume)
            if debug: print "Volume ist NULL"
            break   
        mpd.setvol(volume) 
        time.sleep(1.5)
    
    return(curvol)
        


#-----------------------------------------------
def connect_mpd():
# Connect with MPD (music player daemon)
#------------------------------------------------
    global debug
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
                if debug: print "Couldn't connect. Retrying"
                i=i+1
                if i > retry_count:
                    return(9)
                time.sleep(3)
    if debug: print("Connected to MPD-Server")
    return(0)

#---------------------------------------------------------
# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout


#-----------------------------------------------------------
def blink_led1():  # blink led coninuosly when program runs
    while not exitapp:
        for i in range(3):
            GPIO.output(led1, True)
            time.sleep(0.2)
            GPIO.output(led1, False)
            time.sleep(0.8)
    GPIO.output(led1, False)

#-----------------------------------------------------------
def blink_led2(anzahl,laenge):  # Visual feedback if button pressed and connected
    for i in range(anzahl):
        GPIO.output(led2, True)
        time.sleep(laenge)
        GPIO.output(led2, False)
        time.sleep(0.1)


#-----------------------------------------------------------
def my_callback_nx(channel):
    global starttime, waitstatid
    if debug: print "Pin Falling: %d" % channel
    time.sleep(.2)  # confirm the movement by waiting 1 sec 
    if not GPIO.input(buttonPinNext): # and check again the input
        if debug: print("ok, pin ist tief!")
        ret=client.next()
        blink_led2(2,0.1)
#   button next serves another purpose:        
#   if nextbutton is pressed within 20 seconds after start the wait factor for station ID is set to small (for testing and demo)
        if starttime:
            timenow = time.time()
            elapsed = floor(timenow - starttime)
            if debug: print "%s seconds elapsed" % elapsed
            if elapsed < 20:
                waitstatid=waitstatid_factor_short
                print "Waittime is now short %s", waitstatid
                starttime=0                # do this only once
        
#-----------------------------------------------------------
def my_callback_pr(channel):
    if debug: print "Pin Falling: %d" % channel
    time.sleep(.2)  # confirm the movement by waiting 1 sec 
    if not GPIO.input(buttonPinPrev): # and check again the input
        if debug: print("ok, pin ist tief!")
        client.previous()
        blink_led2(2,0.1)

#-----------------------------------------------------------        
def my_callback_start(channel):
    if debug: print "Pin Falling: %d" % channel
    time.sleep(.2)  # confirm the movement by waiting 1 sec 
    if not GPIO.input(buttonPinStart): # and check again the input
        if debug: print("ok, pin ist tief!")
        client.play(0)
        blink_led2(2,0.1)

#-----------------------------------------------------------
def my_callback_rd(channel):
    global randomstate
    if debug: print "Pin Falling: %d" % channel
    time.sleep(.2)  # confirm the movement by waiting 1 sec 
    if not GPIO.input(buttonPinRandom): # and check again the input
        if debug: print("ok, pin ist tief!")
        if randomstate:
            GPIO.output(led3, False)
            client.random(0)
            randomstate=0
        else:
            GPIO.output(led3, True)
            client.random(1)
            randomstate=1
        
        blink_led2(2,0.1)


#-----------------------------------------------------------            
def connection_status():
#    pings server every 60 seconds and prints "pinging" (if debug is specified).
    global sleep_ping, exitapp
    while not exitapp:  # main thread gives terminate signal here
        if debug: print "Connection: pinging the server"
        client.ping()
        wait=sleep_ping
        while wait > 0:
            time.sleep(3)
            wait=wait-3
#            if debug: print "Connection: Waiting 3 seconds"
            if exitapp: break

    client.close()      # we need to terminate
    if debug: print "-->Thread Connection terminating..."
    sys.exit(0)

#-----------------------------------------------------------    
def button_nx():
    global exitapp
    GPIO.add_event_detect(buttonPinNext, GPIO.FALLING, callback=my_callback_nx, bouncetime=300)
#
    while not exitapp:
        time.sleep(1)
        pass    # pass ist leer statement
        time.sleep(1)
    if debug: print "-->Thread NEXT terminating..."
    sys.exit(0)

#-----------------------------------------------------------
def button_pr():
    global exitapp
    GPIO.add_event_detect(buttonPinPrev, GPIO.FALLING, callback=my_callback_pr, bouncetime=300)
# 
    while not exitapp:   # main thread gives terminate signal here
        time.sleep(1)
        pass    # pass ist leer statement
        time.sleep(1)
    if debug: print "-->Thread PREVIOUS terminating..."
    sys.exit(0)

#-----------------------------------------------------------    
def button_st():
    global exitapp
    GPIO.add_event_detect(buttonPinStart, GPIO.FALLING, callback=my_callback_start, bouncetime=300)
#
    while not exitapp:   # main thread gives terminate signal here
        time.sleep(1)
        pass    # pass ist leer statement
        time.sleep(1)
    if debug: print "-->Thread START PL terminating..."        
    sys.exit(0)

#-----------------------------------------------------------    
def button_rd():
    global exitapp
    GPIO.add_event_detect(buttonPinRandom, GPIO.FALLING, callback=my_callback_rd, bouncetime=300)
#
    while not exitapp:   # main thread gives terminate signal here
        time.sleep(1)
        pass    # pass ist leer statement
        time.sleep(1)
    if debug: print "-->Thread RANDOM terminating..."        
    sys.exit(0)


#-----------------------------------------------------------------
# function (thread) to read pot and set volumne
def read_pot():
    global exitapp, debug, potswitch
# 10k trim pot connected to adc #0
    potentiometer_adc = 0;

    if potswitch: return        # do not ajust volume if switch was on at start (for testing jitter)
    return
        
    last_read = 0       # this keeps track of the last potentiometer value
    tolerance = 10       # to keep from being jittery we'll only change
                    # volume when the pot has moved more than 5 'counts'

    while not exitapp:  # loop til main threads signals termination
        # we'll assume that the pot didn't move
        trim_pot_changed = False

        # read the analog pin
        trim_pot = readadc(potentiometer_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
        # how much has it changed since the last read?
        pot_adjust = abs(trim_pot - last_read)


        if ( pot_adjust > tolerance ):
               trim_pot_changed = True
           

        if ( trim_pot_changed ):
                if debug:   
                    print "Pot tolerance %d  before %s change %s new %s" % (tolerance, trim_pot, (trim_pot - last_read), last_read)
                set_volume = trim_pot / 10.24           # convert 10bit adc0 (0-1024) trim pot read into 0-100 volume level
                set_volume = round(set_volume)          # round out decimal value
                set_volume = int(set_volume)            # cast volume as integer

                if debug: print 'Volume new = {volume}%' .format(volume = set_volume)
                client.setvol(set_volume)
                # save the potentiometer reading for the next loop
                last_read = trim_pot

        # hang out and do nothing for a half second
        time.sleep(1.5)
        
        
# ------------------------------------------------------
# waits randoms seconds and plays station ID
# decreases volume , adds station ID file (mp3) to current playlist, plays it and then deletes it from playlist
# resumes play at next song
def station_id():
    global exitapp, waitstatid

    while not exitapp:   # main thread gives terminate signal here
        waitrandom=random.randint(5, 15)  
        i=1
        # waitstatid can change while running, so loop is a bit crooked.
        while True:
            i=i+1
            waittime=waitrandom*waitstatid-(i*4)
            if waittime > 2: 
                time.sleep(4)
                if debug:  print "StationID: waiting for %d seconds, factor %s" % (waittime,waitstatid)
            else: break
            if exitapp: break
#        ret=connect_mpd(client)
#        if debug: print "Werbung Return from Connect MPD: %d" % ret
        if exitapp: break
        nxid=get_nexid(client)                  # nächstes stück der Playlist holen (ID), wird nach Station ID gespielt
        ident=client.addid("werbung_1.mp3")     # werbung.mp3 zur aktuellen playlist addieren und ID merken
        if debug: print "Station_ID ID: %s" % ident
        cur_vol=lower_volume(client)            # Volume vermindern auf Null, aktuellen Wert vorher speichern      
        client.setvol(cur_vol)                  # Volume wieder erstellen
        if debug: print "Station_ID: Volume reset to %d" % cur_vol
        client.playid(int(ident))               # Play Station ID spielen
        time.sleep(9)                           # warten bis gespielt
        client.playid(nxid)                     # vorher gespeichtertes nächstes Stück spielen
        client.deleteid(int(ident))             # Station ID mp3 entfernen aus der Playlist
        time.sleep(5)
#        client.disconnect()
#        if debug: print " Disconnected from MPD"
    if debug: print "-->Thread Station-ID terminating..."
    sys.exit(0)


#----------------------------------------------------------
def termplay():    # function not used here
    volume=60
    for i in range(15):
        volume=volume-15
        GPIO.output(led2, True)
        time.sleep(0.3)
        GPIO.output(led2, False)
        time.sleep(3)
        print "Set Volume to %d" % volume
        client.setvol(volume)
        time.sleep(3)

#-----------------------------------------------------------
# --------- MAIN --------

arguments(sys.argv[1:])  # get commandline arguments

#GPIO.cleanup(buttonPinNext)  # cleanup GPIO Pins
#GPIO.cleanup(buttonPinPrev)  # cleanup GPIO Pins
#GPIO.cleanup(buttonPinStart)  # cleanup GPIO Pins

GPIO.setwarnings(False)
GPIO.setup(led1, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(led2, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(led3, GPIO.OUT, initial=GPIO.LOW)

GPIO.setup(buttonPinNext, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(buttonPinPrev, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(buttonPinStart, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(buttonPinRandom, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(potschalter, GPIO.IN, pull_up_down=GPIO.PUD_UP)          # switch on Potentiometer

#------------------------------------------------
# set up the SPI interface pins (ADConverter)
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)


time.sleep(1)
# setup mpd Client Object
client = mpd.MPDClient()

ret=connect_mpd()                    # connect to MPD server
if ret==9:
    if debug: print "Could not connect to MPD"
    sys.exit(2)


blink_led2(2,0.5)
# reset random play
client.random(0)
# start play with volume 60%
client.setvol(60)
# clear current playlist
client.clear()
if debug:  print "Playlist cleared"

# check the sitch on the pot: that determines the playlist that we start with. Playlist are predefined
if GPIO.input(potschalter):     # Potswitch it off (ganz links gedreht)
# start playing using playlist Blues-1
    client.load("Blues-1")
    if debug: print "Blues-1 loaded"
else:
# start playing using playlist xmas-1
    client.load("xmas-2")
    if debug: print "xmas-2 loaded"
    potswitch=1                     # potswitch status 1
# start with first song in playlist

client.play(0)                          # play first song in playlist
waitstatid=waitstatid_factor_long       # that can be changed bei pressing the next button with 20 sec after boot.

starttime = time.time()     # save start time

if debug: 
    print "MPD-Version: %s" % client.mpd_version
    print "Wait Factor for Station ID is %s" % waitstatid

# create and Start Threads
connect_thread = Thread(target = connection_status)
button_nx_thread = Thread(target = button_nx)
button_pr_thread = Thread(target = button_pr)
button_st_thread = Thread(target = button_st)
button_rd_thread = Thread(target = button_rd)
station_id_thread = Thread(target = station_id)
led1_thread = Thread(target = blink_led1)
volume_thread = Thread(target = read_pot)


connect_thread.start()          # thread to keep connection to mpd
button_nx_thread.start()        # thread to watch for NEXT button
button_pr_thread.start()        # thread to watch for PREVIOUS button
button_st_thread.start()        # thread to watch for START Playlist button
button_rd_thread.start()        # thread to watch for RANDOM PLAY button
station_id_thread.start()       # thread to play station ID at random intervalls
led1_thread.start()             # thread to blink green led
volume_thread.start()           # thread to read pot and set volume

# Main thread goes into loop (wait for ctrl-C)
# ctrl-C bloss für Tests im Vorground !! 
# posit
try:
    while True:
        time.sleep(3)
        if debug: print "Main thread waiting"
        pass    # pass ist leer statement
        
# somebody wants us to stop doing what we are doing...        
except KeyboardInterrupt:
    # cleanup
    blink_led2(5,0.1)
    exitapp = TRUE      # signal exit to the other threads, they will terminate themselfs
    if debug: print "Main: exitapp Signaled"
    raise
    if debug: print "Main: Terminating, waiting 6 seconds"
    GPIO.cleanup(buttonPinNext)  # cleanup GPIO Pins
    GPIO.cleanup(buttonPinPrev)  # cleanup GPIO Pins
    GPIO.cleanup(buttonPinStart)  # cleanup GPIO Pins
    GPIO.output(led3, False)
    GPIO.cleanup(led1)  # cleanup GPIO Pins
    GPIO.cleanup(led2)  # cleanup GPIO Pins
    GPIO.cleanup(led3)  # cleanup GPIO Pins
    GPIO.cleanup(SPIMOSI)
    GPIO.cleanup(SPIMISO)
    GPIO.cleanup(SPICLK)
    GPIO.cleanup(SPICS)
    client.stop()
   
#    time.sleep(6)       # wait for other threads
    client.disconnect()

    sys.exit(0)

#-----------------------------------------------------------
# The End
#-----------------------------------------------------------
