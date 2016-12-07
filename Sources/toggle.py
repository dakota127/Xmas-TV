import RPi.GPIO as GPIO
from time import sleep

sw1 = 15
sw2=24

led1=9
ledmode=0

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(sw1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(led1, GPIO.OUT, initial=GPIO.LOW)




def blink_led():  # blink led 3 mal bei start und bei shutdown
        for i in range(3):
            GPIO.output(led1, True)
            sleep(0.3)
            GPIO.output(led1, False)
            sleep(0.2)


def toggle_led():  # 
    global ledmode
    if ledmode:
        GPIO.output(led1, False)
        ledmode=0
    else:    
        GPIO.output(led1, True)
        ledmode=1


def my_callback(channel):
    print "Pin Rising: %d" % channel
    sleep(.3)  # confirm the movement by waiting 1 sec 
    if GPIO.input(sw1): # and check again the input
        print("ok, pin ist hoch!")
        toggle_led()

blink_led()
GPIO.add_event_detect(sw1, GPIO.RISING, callback=my_callback, bouncetime=300)

# you can continue doing other stuff here
while True:
    sleep(1)
    pass    # pass ist leer statement
