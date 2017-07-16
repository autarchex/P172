# ThunderCloud - Light and Sound at push of a button on a raspberry pi, to simulate lightning and thunder.
# Pi should be set up to run this at startup just after automatic login.

import RPi.GPIO as gpio

timingfilename = "thundertiming"
thunderevents = {}                  #dictionary stores available thunder events to play
button_pin = 23                     #trigger button input on port 23, active low
heartbeat_pin = 25                  #heartbeat LED output on port 25, active high
lightning1_pin = 26                 #simulated lightning LEDs, bank 1, output on port 26, active high
lightning2_pin = 27                 # "" bank 2


def setup():
    #Setup GPIO
    gpio.setmode(gpio.BCM)
    gpio.setup(button_pin, gpio.IN, pull_up_down=gpio.PUD_UP)   #make port 23 an input with pullup engaged
    gpio.setup(heartbeat_pin, gpio.OUT)
    gpio.setup(lightning1_pin, gpio.OUT)
    gpio.setup(lightning2_pin, gpio.OUT)
    #TODO: set all output pins to zero

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

def mainloop():
    while(True):
        try:
            gpio.wait_for_edge(button_pin, gpio.FALLING)          #wait for falling edge interrupt on button input
        except KeyboardInterrupt:                         #allow a CTRL+C interrupt from keyboard to abort
            gpio.cleanup()                                #place GPIO pins in safe idle state
            return -1                                     #exit to OS
        trigger()                                         #perform actions triggered by button
        #TODO: wait for a few seconds before resuming heartbeat and allowing a new trigger

def trigger():
    #TODO - make OS call to execute 'omxplayer -o local soundfile.mp3 &'  (as background process)
    #TODO - trigger the lights with empirically determined wait times to synch to sound

def playEvent(eventID):
    ev = thunderevents{eventID}
    if ev.hasSound:
        #TODO: execute shell command to play mp3 file with desired parameters, as a separate process.
    #Now process lighting
    if ev.hasLight:
        #TODO: wait for ev.lightDelay seconds doing nothing
        for [off, on] in [ev.lightOffTimes, ev.lightOnTimes]:
            #TODO wait for off seconds
            #TODO raise GPIO line, both banks
            #TODO wait for on seconds
            #TODO drop GPIO line, both banks

class thunder:
    #defines actions to take for a thunder event.
    #Event may consist of light, sound, or both.
    def __init(self):
        self.hasLight = False
        self.hasSound = False
        self.soundfilename = ""
        self.soundStartTime = 0
        self.soundPlayTime = 0
        self.soundVolume = 1
        self.lightDelay = 0
        self.lightOffTimes = []
        self.lightOnTimes = []


#TODO: add 'execute main' code that calls main loop
gpio.cleanup()                                    #place GPIO pins in safe idle state
