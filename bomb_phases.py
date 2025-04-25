#################################
# CSC 102 Defuse the Bomb Project
# GUI and Phase class definitions
# Team: Ellis, Brad, Seb 
#################################

# import the configs
from bomb_configs import *
# other imports
from tkinter import *
import tkinter
from threading import Thread
from time import sleep
import os
import sys
import pygame

#########
# classes
#########
# the LCD display GUI
class Lcd(Frame):
    def __init__(self, window):
        super().__init__(window, bg="black")
        # make the GUI fullscreen
        window.attributes("-fullscreen", True)
        # we need to know about the timer (7-segment display) to be able to pause/unpause it
        self._timer = None
        # we need to know about the pushbutton to turn off its LED when the program exits
        self._button = None
        # setup the initial "boot" GUI
        self.setupBoot()

    # sets up the LCD "boot" GUI
    def setupBoot(self):
        # set column weights
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.columnconfigure(2, weight=1)
        # the scrolling informative "boot" text
        self._lscroll = Label(self, bg="black", fg="white", font=("Courier New", 14), text="", justify=LEFT)
        self._lscroll.grid(row=0, column=0, columnspan=3, sticky=W)
        self.pack(fill=BOTH, expand=True)

    # sets up the LCD GUI
    def setup(self):
        # the timer
        self._ltimer = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Time left: ")
        self._ltimer.grid(row=1, column=0, columnspan=3, sticky=W)
        # the keypad passphrase
        self._lkeypad = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Keypad phase: ")
        self._lkeypad.grid(row=2, column=0, columnspan=3, sticky=W)
        # the jumper wires status
        self._lwires = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Wires phase: ")
        self._lwires.grid(row=3, column=0, columnspan=3, sticky=W)
        # the pushbutton status
        self._lbutton = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Button phase: ")
        self._lbutton.grid(row=4, column=0, columnspan=3, sticky=W)
        # the toggle switches status
        self._ltoggles = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Toggles phase: ")
        self._ltoggles.grid(row=5, column=0, columnspan=2, sticky=W)
        # the strikes left
        self._lstrikes = Label(self, bg="black", fg="#00ff00", font=("Courier New", 18), text="Strikes left: ")
        self._lstrikes.grid(row=5, column=2, sticky=W)
        if (SHOW_BUTTONS):
            # the pause button (pauses the timer)
            self._bpause = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Pause", anchor=CENTER, command=self.pause)
            self._bpause.grid(row=6, column=0, pady=40)
            # the quit button
            self._bquit = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Quit", anchor=CENTER, command=self.quit)
            self._bquit.grid(row=6, column=2, pady=40)

    # lets us pause/unpause the timer (7-segment display)
    def setTimer(self, timer):
        self._timer = timer

    # lets us turn off the pushbutton's RGB LED
    def setButton(self, button):
        self._button = button

    # pauses the timer
    def pause(self):
        if (RPi):
            self._timer.pause()

    # setup the conclusion GUI (explosion/defusion)
    def conclusion(self, success=False):
        # destroy/clear widgets that are no longer needed
        self._lscroll["text"] = ""
        self._ltimer.destroy()
        self._lkeypad.destroy()
        self._lwires.destroy()
        self._lbutton.destroy()
        self._ltoggles.destroy()
        self._lstrikes.destroy()
        if (SHOW_BUTTONS):
            self._bpause.destroy()
            self._bquit.destroy()

        # reconfigure the GUI
        
        if success:
            self._lmessage = tkinter.Label(self, text="You defused the Bomb!", font=("Courier New", 24), fg="green")
            self._lmessage.grid(row=0, column=1, pady=50)
            win_sound = pygame.mixer.Sound("win.wav")
            win_sound.play()
        else:
            self._lmessage = tkinter.Label(self, text="You exploded!", font=("Courier New", 24), fg="green")
            self._lmessage.grid(row=0, column=1, pady=50)
            loss_sound = pygame.mixer.Sound("loss.wav")
            loss_sound.play()
        
        # the retry button
        self._bretry = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Retry", anchor=CENTER, command=self.retry)
        self._bretry.grid(row=1, column=0, pady=40)
        # the quit button
        self._bquit = tkinter.Button(self, bg="red", fg="white", font=("Courier New", 18), text="Quit", anchor=CENTER, command=self.quit)
        self._bquit.grid(row=1, column=2, pady=40)

    # re-attempts the bomb (after an explosion or a successful defusion)
    def retry(self):
        # re-launch the program (and exit this one)
        os.execv(sys.executable, ["python3"] + [sys.argv[0]])
        exit(0)

    # quits the GUI, resetting some components
    def quit(self):
        if (RPi):
            # turn off the 7-segment display
            self._timer._running = False
            self._timer._component.blink_rate = 0
            self._timer._component.fill(0)
            # turn off the pushbutton's LED
            for pin in self._button._rgb:
                pin.value = True
        # exit the application
        exit(0)

# template (superclass) for various bomb components/phases
class PhaseThread(Thread):
    def __init__(self, name, component=None, target=None):
        super().__init__(name=name, daemon=True)
        # phases have an electronic component (which usually represents the GPIO pins)
        self._component = component
        # phases have a target value (e.g., a specific combination on the keypad, the proper jumper wires to "cut", etc)
        self._target = target
        # phases can be successfully defused
        self._defused = False
        # phases can be failed (which result in a strike)
        self._failed = False
        # phases have a value (e.g., a pushbutton can be True/Pressed or False/Released, several jumper wires can be "cut"/False, etc)
        self._value = None
        # phase threads are either running or not
        self._running = False

# the timer phase
class Timer(PhaseThread):
    def __init__(self, component, initial_value, name="Timer"):
        super().__init__(name, component)
        # the default value is the specified initial value
        self._value = initial_value
        # is the timer paused?
        self._paused = False
        # initialize the timer's minutes/seconds representation
        self._min = ""
        self._sec = ""
        # by default, each tick is 1 second
        self._interval = 1

    # runs the thread
    def run(self):
        self._running = True
        while (self._running):
            if (not self._paused):
                # update the timer and display its value on the 7-segment display
                self._update()
                self._component.print(str(self))
                # wait 1s (default) and continue
                sleep(self._interval)
                # the timer has expired -> phase failed (explode)
                if (self._value == 0):
                    self._running = False
                self._value -= 1
            else:
                sleep(0.1)

    # updates the timer (only internally called)
    def _update(self):
        self._min = f"{self._value // 60}".zfill(2)
        self._sec = f"{self._value % 60}".zfill(2)

    # pauses and unpauses the timer
    def pause(self):
        # toggle the paused state
        self._paused = not self._paused
        # blink the 7-segment display when paused
        self._component.blink_rate = (2 if self._paused else 0)
        
    def get_time(self):
        return f"{self._min}:{self._sec}"
    
    def get_current_time(self):
        return self._timer.get_time()


    # returns the timer as a string (mm:ss)
    def __str__(self):
        return f"{self._min}:{self._sec}"

# the keypad phase
class Keypad(PhaseThread):
    def __init__(self, component, target, name="Keypad"):
        super().__init__(name, component, target)
        # the default value is an empty string
        self._value = ""

    # runs the thread
    def run(self):
        self._running = True
        while (self._running):
            # process keys when keypad key(s) are pressed
            if (self._component.pressed_keys):
                # debounce
                while (self._component.pressed_keys):
                    try:
                        # just grab the first key pressed if more than one were pressed
                        key = self._component.pressed_keys[0]
                    except:
                        key = ""
                    sleep(0.1)
                # log the key
                self._value += str(key)
                # the combination is correct -> phase defused
                if (self._value == self._target):
                    self._defused = True
                # the combination is incorrect -> phase failed (strike)
                elif (self._value != self._target[0:len(self._value)]):
                    self._failed = True
            sleep(0.1)

    # returns the keypad combination as a string
    def __str__(self):
        if (self._defused):
            return "DEFUSED"
        else:
            return self._value

# the jumper wires phase
class Wires(PhaseThread):
    def __init__(self, component, target, name="Wires"):
        super().__init__(name, component, target)
        self._last_incorrect = [False] * len(component)  # Track strike per wire

    def run(self):
        self._running = True
        wirecurrentVals = [1] * len(self._component) #All wires start in on/true position

        while self._running:
            for i in range(len(self._component)):
                wirecurrentVals[i] = self._component[i].value

            wiredecimalVal = int("".join(str(int(bit)) for bit in wirecurrentVals), 2) #Converts list of values into decimal int

            if wiredecimalVal == self._target:
                self._defused = True
                return

            targetBits = f"{self._target:0{len(self._component)}b}"[-len(self._component):] #Converts target decimal val into binary string

            #Tracking for strikes
            for i in range(len(wirecurrentVals)):
                # If a wire that should be connected is pulled
                if wirecurrentVals[i] == 0 and targetBits[i] == "1":
                    # Only strike once for this specific wire being pulled
                    if not self._last_incorrect[i]:
                        self._failed = True
                        self._last_incorrect[i] = True
                else:
                    # Reset so it can strike again if the user plugs it back and pulls it again
                    self._last_incorrect[i] = False

            sleep(0.1)


    # returns the jumper wires state as a string
    def __str__(self):
        if self._defused:
            return "DEFUSED"
        else:
            return (f"power source: {wires_hint}")

# the pushbutton phase
class Button(PhaseThread):
    colors = ["R", "G", "B"]  # The button's possible colors

    def __init__(self, state, rgb, year, color=None, target=None, timer=None, name="Button"):
        super().__init__(name)
        self._value = False
        self._state = state
        self._rgb = rgb
        self.year = year
        self.button_color = color  # Accept passed-in color
        self.button_target = target  # Accept passed-in target
        self._timer = timer  # Save the timer reference
        self._defused = False
        self._status = "Active"


        # Ensure LEDs are initially turned off (before the button thread runs)
        self._rgb[0].value = True  # Red LED off
        self._rgb[1].value = True  # Green LED off
        self._rgb[2].value = True  # Blue LED off

    def run(self):
        self._running = True
        prev_value = False  # Track previous button state

        if not self.button_color:
            self.button_color = random.choice(Button.colors)

        # Set LED color
        if self.button_color == "R":
            self._rgb[0].value = False
            self._rgb[1].value = True
            self._rgb[2].value = True
        elif self.button_color == "G":
            self._rgb[0].value = True
            self._rgb[1].value = False
            self._rgb[2].value = True
        elif self.button_color == "B":
            self._rgb[0].value = True
            self._rgb[1].value = True
            self._rgb[2].value = False

        if not self.button_target:
            self.set_button_target()

        while True:
            self._value = self._state.value

            # Button just pressed
            if self._value and not prev_value:
                self._status = "Pressed"

            # Button just released
            elif not self._value and prev_value:
                if not self._defused and self.timer_matches_target():
                    self._defused = True
                    self._status = "Defused"
                    self.led_off()
                elif not self._defused:
                    self._status = "Released"
                    self._failed = True

            prev_value = self._value
            sleep(0.1)




    def set_button_target(self):
        if self.button_color == "R":
            self.button_target = str(self.year)[-1]  # Last digit of the year
        elif self.button_color == "G":
            self.button_target = str(self.year)[-2]  # Second last digit of the year
        elif self.button_color == "B":
            self.button_target = str(self.year)[0]   # First digit of the year

    def timer_matches_target(self):
        current_time = self.get_current_time()
        if current_time[-1] == self.button_target:
            return True
        return False

    def get_current_time(self):
        return str(self._timer._min) + str(self._timer._sec)
    
    def led_off(self):
        self._rgb[0].value = True
        self._rgb[1].value = True
        self._rgb[2].value = True



    def __str__(self):
        return self._status



# the toggle switches phase
class Toggles(PhaseThread):
    def __init__(self, component, target, name="Toggles"):
        super().__init__(name, component, target)
        self._last_incorrect = [False] * len(component)  # Track strike per toggle
        self._initial_check = True  # Flag to skip the first check

    def run(self):
        togglecurrentVals = [0] * len(self._component)  # All toggles start in off position
        self._running = True

        while self._running:
            for i in range(len(self._component)):
                togglecurrentVals[i] = self._component[i].value

            toggledecimalVal = int("".join(str(int(bit)) for bit in togglecurrentVals), 2)  # Converts list of values into decimal int

            # Check if toggles match the target, defuse if so
            if toggledecimalVal == self._target:
                self._defused = True
                return

            # Skip the first check to avoid immediate strikes
            if self._initial_check:
                self._initial_check = False  # Disable first check after the first iteration
                sleep(0.1)  # Wait before checking again (to allow for any interaction)
                continue

            targetBits = f"{self._target:0{len(self._component)}b}"  # Convert target decimal val into binary string

            # Tracking for strikes after the first check
            for i in range(len(togglecurrentVals)):
                if togglecurrentVals[i] != int(targetBits[i]):
                    if not self._last_incorrect[i]:  # Strike only once per incorrect toggle
                        self._failed = True
                        self._last_incorrect[i] = True  # Mark this toggle as incorrect
                else:
                    self._last_incorrect[i] = False  # Reset so it can strike again if flipped back correctly

            sleep(0.1)  # Sleep to avoid too frequent checks

    # returns the toggle switches state as a string
    def __str__(self):
        if self._defused:
            return "DEFUSED"
        else:
            return "Active"