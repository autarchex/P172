# ThunderCloud - Light and Sound at push of a button on a raspberry pi, to simulate lightning and thunder.
# Pi should be set up to run this at startup just after automatic login.

import RPi.GPIO as gpio
from random import randint
import subprocess
import time

localdir = "/home/pi/thunder/"
timingfilename = "thundertiming"
thunderevents = {}                  #dictionary stores available thunder events to play
button_pin = 40                     #trigger button input on port 23, active low
heartbeat_pin = 22                  #heartbeat LED output on port 25, active high
lightning1_pin = 36                 #simulated lightning LEDs, bank 1, output on port 26, active high
lightning2_pin = 32                 # "" bank 2
heartbeat_period = 2


def setup():
    #Setup GPIO
    gpio.setmode(gpio.BOARD)        #use board-relative pin numbering, not SOC-chip-relative numbering
    #gpio.setmode(gpio.BCM)
    gpio.setup(button_pin, gpio.IN, pull_up_down=gpio.PUD_UP)   #make GPIO an input with pullup engaged
    gpio.setup(heartbeat_pin, gpio.OUT, initial=gpio.HIGH)
    gpio.setup(lightning1_pin, gpio.OUT, initial=gpio.LOW)
    gpio.setup(lightning2_pin, gpio.OUT, initial=gpio.LOW)

    #Read in the timing file and build dictionary of playable events
    with open(localdir + timingfilename) as f:
        for line in f:
            tokens = line.strip().split()               #remove whitespace and tokenize
            if len(tokens) < 1:                         #skip empty lines
                continue
            if tokens[0][0] == '#':                     #skip comment lines
                continue
            eventID = int(tokens[0])                    #first value is id number
            linetype = tokens[1]                        #second is type of descriptor line
            if linetype == 'L':                        #line describes Lighting
                print("Found light line for event " + str(eventID) + ":")
                if eventID not in thunderevents.keys():
                    thunderevents[eventID] = thunder()  #create a new event if necessary
                delay = float(tokens[2])        #next argument is synch delay
                thunderevents[eventID].lightDelay = delay
                print("Synch delay " + str(delay) + " seconds...")
                times = tokens[3:]
                for t1,t2 in zip(times[::2], times[1::2]):             #arrange times into pairs
                    print("Wait " + str(t1) + " seconds, then turn light on for " + str(t2) + " seconds...")
                    thunderevents[eventID].lightOffTimes.append(float(t1)) #first is a light-off duration
                    thunderevents[eventID].lightOnTimes.append(float(t2))  #next is a light-on duration
                thunderevents[eventID].hasLight = True
                print("***** End of lighting for event " + str(eventID))

            elif linetype == 'S':                      #line describes sound
                print("Found sound line for event " + str(eventID))
                filename = tokens[2]                    #next argument is mp3 file name
                starttime = tokens[3]
                duration = tokens[4]
                volume = tokens[5]
                print("Play file: " + filename + " ...")
                print("Start playback at " + str(starttime) + " seconds, for " + str(duration) + " seconds, at volume=" + str(volume))
                print("(Ignored duration value, this is not implemented.)")
                print("(Ignored start time value, this is not implemented.)")
                print("***** End of sound for event " + str(eventID))
                if eventID not in thunderevents.keys():
                    thunderevents[eventID] = thunder()  #create a new event and add to dictionary
                thunderevents[eventID].soundfilename = localdir + filename
                thunderevents[eventID].soundStartTime = starttime
                thunderevents[eventID].soundPlayTime = duration
                thunderevents[eventID].soundVolume = volume
                thunderevents[eventID].hasSound = True
            else:                                       #mis-formed input line
                continue

def main():
    heartbeat_last = 0
    heartbeat_state = 0
    while(True):                                           #loop forever
        if not gpio.input(button_pin):                  #button press? (active low)
            trigger()                                   #then do the thing!  It takes a while (5-30 seconds)
        #manage heartbeat LED
        now = time.time()
        if (now - heartbeat_last) > (heartbeat_period / 2):
            heartbeat_last = now
            if heartbeat_state == 1:
                heartbeat_state = 0
            else:
                heartbeat_state = 1
            gpio.output(heartbeat_pin, heartbeat_state)


def trigger():
    keys = list(thunderevents.keys())
    print("Triggered!")
    if not keys:
        print("ERROR - No events available to play.")
        return
    print("Keys: " + str(keys))
    selected = randint(0, len(keys)-1)      #randomly select one
    print("Selected: " + str(selected))
    evID = keys[selected]              #get its ID number
    print("evID: " + str(evID))
    ev = thunderevents[evID]                            #get the selected event object
    if ev.hasSound:
        args = ["omxplayer"]
        if ev.soundStartTime != 0:
            args.append("--pos")
            args.append(str(ev.soundStartTime))  #TODO: make sure this works without hh:mm:ss formatters
        if ev.soundVolume != 0:
            args.append("--vol")
            args.append(str(ev.soundVolume))     #initial volume in millibels
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
    def __init__(self):
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
    setup()                             #one-time startup stuff
    main()                              #ideally this does not return
    gpio.cleanup()                      #just in case it does return
