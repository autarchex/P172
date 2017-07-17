# ThunderCloud - Light and Sound at push of a button on a raspberry pi, to simulate lightning and thunder.
# Pi should be set up to run this at startup just after automatic login.

import RPi.GPIO as gpio
from random import randint
import subprocess
import time

timingfilename = "thundertiming"
thunderevents = {}                  #dictionary stores available thunder events to play
button_pin = 23                     #trigger button input on port 23, active low
heartbeat_pin = 25                  #heartbeat LED output on port 25, active high
lightning1_pin = 26                 #simulated lightning LEDs, bank 1, output on port 26, active high
lightning2_pin = 27                 # "" bank 2
heartbeat_period = 2
heartbeat_state = 0
heartbeat_lasttime = 0


def setup():
    #Setup GPIO
    gpio.setmode(gpio.BOARD)        #use board-relative pin numbering, not SOC-chip-relative numbering
    #gpio.setmode(gpio.BCM)
    gpio.setup(button_pin, gpio.IN, pull_up_down=gpio.PUD_UP)   #make port 23 an input with pullup engaged
    gpio.setup(heartbeat_pin, gpio.OUT, initial=gpio.LOW)
    gpio.setup(lightning1_pin, gpio.OUT, initial=gpio.HIGH)
    gpio.setup(lightning2_pin, gpio.OUT, initial=gpio.LOW)
    #prepare heartbeat function
    heartbeat_last = time.time()

    #Read in the timing file and build dictionary of playable events
    with open(timingfilename) as f:
        for line in f:
            tokens = line.strip()                       #remove whitespace and tokenize
            if tokens[0][0] == '#':                     #skip comment lines
                continue
            eventID = int(tokens[0])                    #first value is id number
            if tokens[1] == 'L':                        #line describes Lighting
                delay = tokens[2]                       #next argument is synch delay
                if eventID not in thunderevents.keys():
                    thunderevents{eventID} = thunder()  #create a new event if necessary
                thunderevents{eventID}.lightDelay = delay
                for [t1, t2] in tokens[3:]:             #arrange remaining tokens into pairs
                    thunderevents{eventID}.lightOffTimes.append(t1) #first is a light-off duration
                    thunderevents{eventID}.lightOnTimes.append(t2)  #next is a light-on duration
                thunderevents{eventID}.hasLight = True
            elif tokens[1] == 'S':                      #line describes sound
                filename = tokens[2]                    #next argument is mp3 file name
                starttime = tokens[3]
                duration = tokens[4]
                volume = tokens[5]
                if eventID not in thunderevents.keys():
                    thunderevents{eventID} = thunder()  #create a new event and add to dictionary
                thunderevents{eventID}.soundfilename = filename
                thunderevents{eventID}.soundStartTime = starttime
                thunderevents{eventID}.soundPlayTime = duration
                thunderevents{eventID}.soundVolume = volume
                thunderevents{eventID}.hasSound = True
            else:                                       #mis-formed input line
                continue

def main():
    while(True):                                           #loop forever
        if not gpio.input(button_pin):                  #button press? (active low)
            trigger()                                   #then do the thing!  It takes a while (5-30 seconds)
        now = time.time()
        #check if it is time to flip the heartbeat LED, do so if needed
        if (now - heartbeat_last) > (heartbeat_period / 2):
            if heartbeat_state == 1:
                heartbeat_state = 0
            else:
                heartbeat_state = 1
            gpio.output(heartbeat_pin, heartbeat_state)


def trigger():
    selected = randint(0, len(thunderevents.keys())      #randomly select one
    eventID = thunderevents.keys()[selected]              #get its ID number
    ev = thunderevents{eventID}                            #get the selected event object
    if ev.hasSound:
        args = ["omxplayer"]
        if ev.soundStartTime != 0:
            args.append("--pos " + str(ev.soundStartTime))  #TODO: make sure this works without hh:mm:ss formatters
        if ev.soundVolume != 0:
            args.append("--vol " + str(ev.soundVolume))     #initial volume in millibels
        args.append(ev.soundfilename)
        subprocess.Popen(args)                              #should run concurrently (background process)
    #Now process lighting
    if ev.hasLight:
        time.sleep(ev.lightDelay)                   #wait for light-sound synch delay to expire
        for offtime, ontime in zip(ev.lightOffTimes, ev.lightOnTimes):  #operate on off/on pairs
            time.sleep(offtime)             #spend some time with lights off
            gpio.output(lightning1_pin, gpio.HIGH)  #turn the lights on
            gpio.output(lightning2_pin, gpio.HIGH)
            time.sleep(ontime)              #keep lights on for a while
            gpio.output(lightning1_pin, gpio.LOW)   #turn the lights back off
            gpio.output(lightning2_pin, gpio.LOW)

class thunder:
    #defines actions to take for a thunder event.
    #Event may consist of light, sound, or both.
    def __init(self):
        self.hasLight = False
        self.hasSound = False
        self.soundfilename = ""
        self.soundStartTime = 0
        self.soundPlayTime = 0
        self.soundVolume = 0
        self.lightDelay = 0
        self.lightOffTimes = []
        self.lightOnTimes = []


#TODO: add 'execute main' code that calls main loop
if __name__ == '__main__':
    main()                              #ideally this does not return
    gpio.cleanup()                      #just in case it does return
