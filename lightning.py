
#Cloud Lightning main script
#Waits for button press, activates light and sound on press, then resets.


import RPi.GPIO as gpio

gpio.setmode(gpio.BCM)

gpio.setup(23,gpio.IN, pull_up_down=gpio.PUD_UP)  #port 23, input, with pull-up enabled

#TODO - set up a heartbeat output pin
#TODO - set up a light string output trigger pin

while(True):

    try:
        gpio.wait_for_edge(23, gpio.FALLING)          #wait (using interrupts) for falling edge
    except KeyboardInterrupt:                         #allow a CTRL+C interrupt from keyboard to terminate
        gpio.cleanup()                                #place GPIO pins in safe idle state
        return -1                                     #exit to OS

#TODO - make OS call to execute 'omxplayer -o local soundfile.mp3 &'  (as background process)
#TODO - trigger the lights with empirically determined wait times to synch to sound



gpio.cleanup()                                    #place GPIO pins in safe idle state

