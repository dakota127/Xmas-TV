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
from threading import Thread

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
def connection_status():
#    pings server every 60 seconds and prints "pinging" (if debug is specified).
    global sleep_ping
    while not exitapp:  # main thread gives terminate signal here
        if debug: print "pinging the server"
        client.ping()
        time.sleep(sleep_ping)
    client.close()      # we need to terminate
    sys.exit(0)


#-----------------------------------------------------------            
def lower_volume():
    status = client.status()
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
            client.setvol(volume)
            print "Vol ist NULL"
            break   
        client.setvol(volume) 



#-----------------------------------------------------------
# --------- MAIN --------

arguments(sys.argv[1:])  # get commandline arguments

GPIO.setwarnings(False)
GPIO.setup(led1, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(led2, GPIO.OUT, initial=GPIO.LOW)

time.sleep(1)
client = mpd.MPDClient()

# Connect with MPD
#-----------------
connected = False
while connected == False:
        connected = True
        try:
             client.connect(TEST_MPD_HOST, TEST_MPD_PORT)
        except SocketError as e:
             connected = False
        if connected == False:
                print "Couldn't connect. Retrying"
            
                time.sleep(5)
if debug: print("Connected to MPD-Server")

# reset random play
client.random(0)

if debug: print "MPD-Version: %s" % client.mpd_version


volume=0


        





# Start Threads and catch ctlr-C
# posit
try:
    connect_thread = Thread(target = connection_status)
   
    led1_thread = Thread(target = blink_led1)

    connect_thread.start()
    led1_thread.start()

    client.setvol(volume)

    for i in range(15):
        volume=volume+5
        GPIO.output(led2, True)
        time.sleep(0.3)
        GPIO.output(led2, False)
        time.sleep(0.5)
        print "Set Volume to %d" % volume
        client.setvol(volume)

        
    client.volume(-10)   
    print 'Volume-----------------------------------------------------------------'
    lower_volume()
    time.sleep(2)
     
    idend=client.add("file:///var/end_tv.mp3")
    print "ID: %" %idend
     
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