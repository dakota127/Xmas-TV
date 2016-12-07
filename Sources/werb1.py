#!/usr/bin/python
# coding: utf-8
#------------------------------------------------------
# Client for mpd-Server
#   waits für button click on three buttons - sets up three interrupt routines
#   button 1 (GPIO23) :  jump to next title in playlist
#   button 2 (GPIO24) :  jump to previuos title in playlist
#   button 3  (GPIO8) :  jump to first title in playlist
#
#   Led1 blinks as long as program runs
#   Pressing a buttons blinks Led2 twice for visual feedback
#   Successful connection to mpd Server blinks Led2 twice
#   keyboard Interrupt is catched for testing purposes in Terminal
#   Script is started via /etc/rc.local
#
#   Simple Version found on the Volumio-Forum
#   Extended and adapted by Peter K. Boxler, November 2014 
#-------------------------------------------------------

import RPi.GPIO as GPIO
import sys, getopt, os
import mpd
import time
import random
from mpd import MPDClient

GPIO.setmode(GPIO.BCM)
buttonPinNext 	= 8
buttonPinPrev 	= 24
buttonPinStart 	= 23
buttonPinRandom = 15

debug = 0
led1=25
led2=7
led3=9
FALSE=0
TRUE=1
exitapp = FALSE
sleep_ping=30
randomstate=0

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
def blink_led1():  # blink led coninuosly when program runs
    while not exitapp:
        for i in range(3):
            GPIO.output(led1, True)
            time.sleep(0.2)
            GPIO.output(led1, False)
            time.sleep(0.8)
    GPIO.output(led1, False)

#-----------------------------------------------------------
def blink_led2(anzahl,laenge):  # Visual feedback if buuton pressed and connected
    for i in range(anzahl):
        GPIO.output(led2, True)
        time.sleep(laenge)
        GPIO.output(led2, False)
        time.sleep(0.1)

#-----------------------------------------------------------            
def get_nexid(mpd):
    status = mpd.status()
    for text in status:
            if text=="nextsongid":
                nexid=int(status.get(text))
                print "Next SongID: %d" % nexid 
    return(nexid)


#-----------------------------------------------------------            
def lower_volume(mpd):
    status = mpd.status()
    for text in status:
            if text=="volume":
                curvol=int(status.get(text))
                print "Current Volume: %d" % curvol 
    volume=curvol
    print "deceasing"
    while TRUE:
        volume=volume-10
        if volume<0: 
            volume=0
            mpd.setvol(volume)
            print "Vol ist NULL"
            break   
        mpd.setvol(volume) 
        time.sleep(1.5)
    
    return(curvol)
        
#-----------------------------------------------------------            
def get_current_song(mpd):
    status = mpd.status()
    for text in status:
            if text=="volume":
                curvol=int(status.get(text))
                print "Current Volume: %d" % curvol 
    volume=curvol
    print "deceasing"
        

#-----------------------------------------------
def connect_mpd(mpd):
# Connect with MPD
#------------------------------------------------
    global debug
    connected = False
    retry_count=3
    i=1
    while connected == False:
        connected = True
        try:
             mpd.connect(TEST_MPD_HOST, TEST_MPD_PORT)
        except SocketError as e:
             connected = False
        if connected == False:
                if debug: print "Couldn't connect. Retrying"
                i=i+1
                if i > retry_count:
                    return(9)
                time.sleep(3)
    if debug: print("Connected to MPD-Server")
    if debug: print "MPD-Version: %s" % mpd.mpd_version
    return(0)
        
#-----------------------------------------------------------
# --------- MAIN --------

arguments(sys.argv[1:])  # get commandline arguments

GPIO.setwarnings(False)
GPIO.setup(led1, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(led2, GPIO.OUT, initial=GPIO.LOW)

time.sleep(1)
client = MPDClient()               # create client object
client.timeout = 10                # network timeout in seconds (floats allowed), default: None
client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default:$
ret=connect_mpd(client)
if debug: print "Return from Connect MPD: %d" % ret


# reset random play
client.random(0)


volume=40


# posit
try:
    time.sleep(5)
    nxid=get_nexid(client)
 
    ident=client.addid("werbung_1.mp3")
    print "ID: %s" % ident
    cur_vol=lower_volume(client)

    client.setvol(cur_vol)
        
    client.playid(int(ident)) 
    time.sleep(9)
    client.playid(nxid)
    client.deleteid(int(ident))
    if debug: print "Volume reset to %d" % cur_vol
    exitapp= TRUE
    while TRUE:
        time.sleep(1)
        pass
        
# somebody wants us to stop doing what we are doing...        
except KeyboardInterrupt:
    # cleanup
    blink_led2(5,0.1)
    exitapp = TRUE
    raise
    if debug: print "Terminating..."
    GPIO.output(led3, False)
    GPIO.cleanup(led1)  # cleanup GPIO Pins
    GPIO.cleanup(led2)  # cleanup GPIO Pins
    GPIO.cleanup(led3)  # cleanup GPIO Pins
    client.disconnect()

    sys.exit(0)

#-----------------------------------------------------------
# The End
#-----------------------------------------------------------