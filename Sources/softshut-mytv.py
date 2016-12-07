#!/usr/bin/python
# coding: utf-8
#------------------------------------------------------
#   Pi Soft Shutdown Script
#
#   Initiate Shutdown, Play Bye Bye song before shutting down
#
#   Script started at boot via /etc/rc.local
#
#   Peter Boxler, Dezember 2014
#-------------------------------------------------------
#
# Import the modules to send commands to the system and access GPIO pins
from subprocess import call
import RPi.GPIO as gpio
from time import sleep
import sys, getopt
from mpd import MPDClient



# Define variables to store the pin numbers

# for my TV Project
soft_shutdown_pin = 11 # Default pin for Pi Supply is 30 (war 7/16)
soft_shutdown_led = 10   #for visual feebdack  ----> 
#
#from time import sleep
import RPi.GPIO as GPIO
var=1
global debug
debug=0
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
            print ("App softshut-mytv -----------------------------------")
            print ("usage: softshut-mytv [-s -h]")
            sys.exit(2)
        elif opt == '-d': 	debug = 1
	
# ***********************************************

# Define a function to run when an interrupt is called
def shutdown():
#    call(['shutdown', '-hP','+0.5'], shell=False)
    if debug: print "sleeping 4 secs"
    sleep(4)        # zeit geben den prozessen
    if debug:
        print "Shutdown here"
        sleep(3)
    else:    
        if debug: print "Doing Shutdown now"
        call('halt', shell=False)
        pass
        
#-------------------------------------------------------        
def blink_led():  # blink led 3 mal bei start und bei shutdown
        for i in range(3):
            GPIO.output(soft_shutdown_led, True)
            sleep(0.2)
            GPIO.output(soft_shutdown_led, False)
            sleep(0.2)
    

def my_callback(channel):
    if debug: print "shutdown Pin Falling: %d" % channel
    sleep(1.5)  # confirm the movement by waiting 1 sec 
    if not GPIO.input(soft_shutdown_pin): # and check again the input
        if debug: print("ok, shutdownpin ist tief!")
        blink_led()   
        sleep(2)
        client = MPDClient()               # create client object
        client.timeout = 10                # network timeout in seconds (floats allowed), default: None
        client.idletimeout = None          # timeout for fetching the result of the idle command is handled seperately, default:$
        ret=connect_mpd(client)
        if debug: print "Return from Connect MPD: %d" % ret
        lower_volume(client)                # lower Volume to zero
        client.setvol(60)                   # set Volume to 60% for bye bye Song (Text)
        ident=client.addid("end_tv.mp3")    # load mp3 into playlist, store song id
        if debug: print "Endplay ID: %s" % ident
        client.playid(int(ident))           # play bye bye song
        sleep(4)
        client.deleteid(int(ident))         # delete song from paylist
        client.stop()                    # stop playing

        client.disconnect()                 # disconnect from mpd
        shutdown()                          # initiate Pi shutdown

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
                if debug: print "Couldn't connect to MPD. Retrying"
                i=i+1
                if i > retry_count:
                    return(9)
                sleep(3)
    if debug: print("Connected to MPD-Server")
    return(0)


#-----------------------------------------------------------            
def lower_volume(mpd):
    global debug
    status = mpd.status()
    for text in status:
            if text=="volume":
                curvol=int(status.get(text))
                if debug: print "Current Volume: %d" % curvol 
    volume=curvol
    if debug: print "Volume decreasing"
    while True:
        volume=volume-10
        if volume<0: 
            volume=0
            mpd.setvol(volume)
            if debug: print "Volume ist NULL"
            break   
        mpd.setvol(volume) 
        sleep(1.5)


#-----------------------------------------------------------
# --------- MAIN --------

arguments(sys.argv[1:])  # get commandline arguments
if debug: print" Running with debug on"
#
# setup GPIO Pins
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(soft_shutdown_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(soft_shutdown_led, GPIO.OUT, initial=GPIO.LOW)
sleep(5)


blink_led()
# add callback für Shutdown Pushbutton on Pin
GPIO.add_event_detect(soft_shutdown_pin, GPIO.FALLING, callback=my_callback, bouncetime=300)

# you can continue doing other stuff here
while True:
    sleep(1)
    pass    # pass ist leer statement
    
#  ---------------------------------------------
#  End of Program
#-----------------------------------------------