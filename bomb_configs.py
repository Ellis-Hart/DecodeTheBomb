#################################
# CSC 102 Defuse the Bomb Project
# Configuration file
# Team: Ellis, Brad, Seb
#################################

# constants
DEBUG = False        # debug mode?
RPi = True           # is this running on the RPi?
ANIMATE = True       # animate the LCD text?
SHOW_BUTTONS = False # show the Pause and Quit buttons on the main LCD GUI?
COUNTDOWN = 300      # the initial bomb countdown value (seconds)
NUM_STRIKES = 6      # the total strikes allowed before the bomb "explodes"
NUM_PHASES = 4       # the total number of initial active bomb phases

# imports
import random
import string
if (RPi):
    import board
    from adafruit_ht16k33.segments import Seg7x4
    from digitalio import DigitalInOut, Direction, Pull
    from adafruit_matrixkeypad import Matrix_Keypad

#################################
# setup the electronic components
#################################
# 7-segment display
# 4 pins: 5V(+), GND(-), SDA, SCL
#         ----------7SEG---------
if (RPi):
    i2c = board.I2C()
    component_7seg = Seg7x4(i2c)
    # set the 7-segment display brightness (0 -> dimmest; 1 -> brightest)
    component_7seg.brightness = 0.5

# keypad
# 8 pins: 10, 9, 11, 5, 6, 13, 19, NA
#         -----------KEYPAD----------
if (RPi):
    # the pins
    keypad_cols = [DigitalInOut(i) for i in (board.D10, board.D9, board.D11)]
    keypad_rows = [DigitalInOut(i) for i in (board.D5, board.D6, board.D13, board.D19)]
    # the keys
    keypad_keys = ((1, 2, 3), (4, 5, 6), (7, 8, 9), ("*", 0, "#"))

    component_keypad = Matrix_Keypad(keypad_rows, keypad_cols, keypad_keys)

# jumper wires
# 10 pins: 14, 15, 18, 23, 24, 3V3, 3V3, 3V3, 3V3, 3V3
#          -------JUMP1------  ---------JUMP2---------
# the jumper wire pins
if (RPi):
    # the pins
    component_wires = [DigitalInOut(i) for i in (board.D14, board.D15, board.D18, board.D23, board.D24)]
    for pin in component_wires:
        # pins are input and pulled down
        pin.direction = Direction.INPUT
        pin.pull = Pull.DOWN

# pushbutton
# 6 pins: 4, 17, 27, 22, 3V3, 3V3
#         -BUT1- -BUT2-  --BUT3--
if (RPi):
    # the state pin (state pin is input and pulled down)
    component_button_state = DigitalInOut(board.D4)
    component_button_state.direction = Direction.INPUT
    component_button_state.pull = Pull.DOWN
    # the RGB pins
    component_button_RGB = [DigitalInOut(i) for i in (board.D17, board.D27, board.D22)]
    for pin in component_button_RGB:
        # RGB pins are output
        pin.direction = Direction.OUTPUT
        pin.value = True

# toggle switches
# 3x3 pins: 12, 16, 20, 21, 3V3, 3V3, 3V3, 3V3, GND, GND, GND, GND
#           -TOG1-  -TOG2-  --TOG3--  --TOG4--  --TOG5--  --TOG6--
if (RPi):
    # the pins
    component_toggles = [DigitalInOut(i) for i in (board.D12, board.D16, board.D20, board.D21)]
    for pin in component_toggles:
        # pins are input and pulled down
        pin.direction = Direction.INPUT
        pin.pull = Pull.DOWN

###########
# functions
###########

# generates the bomb's serial number

def genSerial():
    #Generates a random year to hide within serial number. Used as a clue for keypad.
    year = str(random.randint(2020, 2025))
    
    #Generate random segments
    prefix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    middle = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    #Choose random positions to insert the word bomb and the year
    parts = [prefix, middle, suffix]
    insert_positions = random.sample([0, 1, 2], 2)
    parts[insert_positions[0]] += "bomb"
    parts[insert_positions[1]] += year
    
    #Shuffle parts for added randomness
    random.shuffle(parts)
    serial = '-'.join(parts)
    return serial, year

def genSysModel():
    while True:
        digits = [random.randint(0, 9) for i in range(3)]  # Generate 3 digits
        total = sum(digits)
        if 1 <= total <= 15:
            model_str = "".join(str(d) for d in digits)
            SysModel = f"{model_str}BOMBv4.2"
            toggles_target = total
            return SysModel, toggles_target


def genWireTarget():
    buildingNo = random.randint(1, 31) #Generates a random int from 0-30 to be the target val for wires
    buildings = [ "Athletic Offices", "Baseball Field", "Beach Volleyball Complex", "Aquatic Center", "Recreation Center", "Cass Gymnasium",
                  "Athletics Center", "Tennis Complex", "Intramural Complex", "Softball Complex", "Pepin Stadium", "Pickleball Courts",
                  "Track", "Austin Hall", "Barrymore Hotel", "Brevard Hall", "Grand Center", "Jenkins Hall", "McKay Hall", "Morsani Hall",
                  "Palm Apartments", "Smiley Hall", "Straz Hall", "Urso Hall", "Vaughn Center", "Admissions", "Bailey Art Studios", "Bookstore",
                  "Campus Safety", "Cass Building", "Central Receiving"]
    buildingClue = buildings[buildingNo-1]
    return buildingNo, buildingClue

# Morse Code Dictionary for letters
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---',
    'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.'
}

def genKeypadCombination():
    # Encrypts a keyword using Morse Code
    def morse_encrypt(keyword):
        morse_keyword = ""
        for letter in keyword.upper():
            if letter in MORSE_CODE_DICT:
                morse_keyword += MORSE_CODE_DICT[letter] + " "  # Add space between each Morse code letter
        return morse_keyword.strip()  # Strip trailing space

    # Returns the keypad digits that correspond to the keyword
    def digits(keyword):
        combination = ""
        keys = [ None, None, "ABC", "DEF", "GHI", "JKL", "MNO", "PRS", "TUV", "WXY" ]
        
        # Process each character of the keyword
        for c in keyword.upper():
            for i, k in enumerate(keys):
                if k and c in k:
                    # Map each character to its digit equivalent
                    combination += str(i)
        
        return combination

    # List of possible keywords
    keywords = [ "ARRAY", "BYTE", "CACHE", "CODING", "COMPILE", "DATABASE", "DEBUG", "LIBRARY", "NETWORK", "PYTHON", 
                 "REBOOT", "SERVER", "SPARTAN", "SYSTEM", "TAMPA", "ZIPBOMB" ]

    # Randomly select a keyword from the list
    keyword = random.choice(keywords)

    # Encrypt the keyword using Morse Code
    cipher_keyword = morse_encrypt(keyword)

    # Generate the corresponding keypad combination from the keyword
    keypad_target = digits(keyword)

    return keyword, cipher_keyword, keypad_target

###############################
# generate the bomb's specifics
###############################
# generate the bomb's serial number (which also gets us the toggle and jumper target values)
#  serial: the bomb's serial number
#  toggles_target: the toggles phase defuse value
#  wires_target: the wires phase defuse value
serial, year = genSerial()
SysModel, toggles_target = genSysModel()
wires_target, wires_hint = genWireTarget()

# generate the combination for the keypad phase
#  keyword: the plaintext keyword
#  cipher_keyword: morse code combination
#  keypad_target: the keypad phase defuse value (combination)
keyword, cipher_keyword, keypad_target = genKeypadCombination()

# generate the color of the pushbutton (which determines how to defuse the phase)
button_color = random.choice(["R", "G", "B"])

# The button target is derived from the timer based on color:
# R: last digit of seconds
# G: first digit of seconds
# B: minutes digit
# We'll store which part of the time to match for use in the phase logic

if button_color == "R":
    button_target = year[-1]
elif button_color == "G":
    button_target = year[-2]
elif button_color == "B":
    button_target = year[0]


if (DEBUG):
    print(f"Serial number: {serial}")
    print(f"Toggles target: {bin(toggles_target)[2:].zfill(4)}/{toggles_target}")
    print(f"Wires target: {bin(wires_target)[2:].zfill(5)}/{wires_target}")
    print(f"Keypad target: {keypad_target}/{passphrase}/{keyword}/{cipher_keyword}(rot={rot})")
    print(f"Button target: {button_target}")

# set the bomb's LCD bootup text
boot_text = f"Booting...\n\x00\x00"\
            f"*Kernel v3.1.4-159 loaded.\n"\
            f"Initializing subsystems...\n\x00"\
            f"*System model: {SysModel}\n"\
            f"*Serial number: {serial}\n"\
            f"Encrypting keypad...\n\x00"\
            f"*Keyword: {cipher_keyword}\n"\
            f"*{' '.join(string.ascii_uppercase)}\n"\
            f"*{' '.join([str(n % 10) for n in range(26)])}\n"\
            f"Rendering phases...\x00"
