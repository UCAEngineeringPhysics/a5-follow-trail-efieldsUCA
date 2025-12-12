# File: main.py
from encoded_motor import EncodedMotor
from hri_controller import HRIController
from ultrasonic_ranger import UltrasonicRanger
from machine import Pin
from time import sleep, ticks_ms, ticks_diff
import math

# -------------------------------------
# Robot Constants
# -------------------------------------
wheel_radius = 0.0235      # meters
gear_ratio = 98.6
CPR = 28
axle_length = 0.125         # meters

# -------------------------------------
# LED & Sensor Pin Setup
# -------------------------------------
HRI_BUTTON_PIN = 4
HRI_LED_PINS = (16, 17, 18)
ULTRASONIC_TRIG_PIN = 3
ULTRASONIC_ECHO_PIN = 2
ULTRASONIC_LED_PINS = (19, 20, 21)

# Initialize Objects
hri = HRIController(HRI_BUTTON_PIN, HRI_LED_PINS)
ranger = UltrasonicRanger(ULTRASONIC_TRIG_PIN, ULTRASONIC_ECHO_PIN, ULTRASONIC_LED_PINS)

# -------------------------------------
# Motor Setup
# -------------------------------------
left = EncodedMotor(
    driver_ids=(7, 9, 8),
    encoder_ids=(27, 28)
)

right = EncodedMotor(
    driver_ids=(15, 13, 14),
    encoder_ids=(22, 26)
)

STBY = Pin(12, Pin.OUT)
STBY.on()

# -------------------------------------
# Encoder Math
# -------------------------------------
def linear_target_counts(distance_m):
    return (distance_m / (2 * math.pi * wheel_radius)) * gear_ratio * CPR

def spin_target_counts(theta_rad):
    arc = (axle_length / 2) * theta_rad
    Cl = -(arc / (2 * math.pi * wheel_radius)) * gear_ratio * CPR
    Cr = +(arc / (2 * math.pi * wheel_radius)) * gear_ratio * CPR
    return Cl, Cr

# -------------------------------------
# Helpers
# -------------------------------------
def reset_encoders():
    left.reset_encoder_counts()
    right.reset_encoder_counts()
    sleep(0.05)

def stop_all():
    left.stop()
    right.stop()
    # Turn off all LEDs when stopped
    hri._set_color(0, 0, 0)
    ranger._set_color(0, 0, 0)

def visual_countdown(seconds=5):
    """Counts down with colors: Red -> Orange -> Green -> White Flash"""
    for i in range(seconds, 0, -1):
        print(f"Starting in {i}...")
        if i > 2:   # RED
            hri._set_color(65535, 0, 0)
            ranger._set_color(1, 0, 0)
        elif i == 2: # ORANGE
            hri._set_color(65535, 16000, 0) 
            ranger._set_color(1, 1, 0)
        else:       # GREEN
            hri._set_color(0, 65535, 0)
            ranger._set_color(0, 1, 0)
            
        sleep(0.9)
        hri._set_color(0, 0, 0)
        ranger._set_color(0, 0, 0)
        sleep(0.1)

    print("GO!")
    hri._set_color(65535, 65535, 65535) # White Flash
    ranger._set_color(1, 1, 1)
    sleep(0.5)
    hri._set_color(0, 0, 0)
    ranger._set_color(0, 0, 0)

# -------------------------------------
# Movement Functions
# -------------------------------------
def drive_straight(distance_m, speed=0.5):
    reset_encoders()
    target = abs(linear_target_counts(distance_m))

    left.forward(speed)
    right.forward(speed)

    # --- LED Setup for Driving ---
    last_led_time = ticks_ms()
    led_state = False

    while True:
        lc = abs(left.encoder_counts)
        rc = abs(right.encoder_counts)

        # --- "HYPER-DRIVE" FLASHING LOGIC ---
        # Strobe every 150ms
        current_time = ticks_ms()
        if ticks_diff(current_time, last_led_time) > 150:
            last_led_time = current_time
            led_state = not led_state
            
            if led_state:
                # Color 1: BLUE
                hri._set_color(0, 0, 65535)
                ranger._set_color(0, 0, 1)
            else:
                # Color 2: MAGENTA (Red + Blue)
                hri._set_color(65535, 0, 65535) 
                ranger._set_color(1, 0, 1)
        # -------------------------------------

        # Straight-line correction
        if lc > rc + 3:
            left.forward(speed - 0.07)
            right.forward(speed)
        elif rc > lc + 3:
            right.forward(speed - 0.07)
            left.forward(speed)
        else:
            left.forward(speed)
            right.forward(speed)

        if lc >= target and rc >= target:
            break
            
        sleep(0.001)

    stop_all()

def spin(theta_rad, speed=0.45):
    reset_encoders()
    Cl, Cr = spin_target_counts(theta_rad)

    direction = "LEFT" if theta_rad > 0 else "RIGHT"
    print(f"Turning {direction} (Signal On)")

    if Cl < 0: left.backward(speed)
    else:      left.forward(speed)

    if Cr < 0: right.backward(speed)
    else:      right.forward(speed)

    # -- Turn Signal Setup --
    last_blink_time = ticks_ms()
    led_state = False

    while True:
        lc = left.encoder_counts
        rc = right.encoder_counts

        # --- AMBER BLINKING LOGIC ---
        current_time = ticks_ms()
        if ticks_diff(current_time, last_blink_time) > 200:
            last_blink_time = current_time
            led_state = not led_state 
            
            if led_state:
                # Signal ON (Amber)
                hri._set_color(65535, 16000, 0) 
                ranger._set_color(1, 1, 0)
            else:
                # Signal OFF
                hri._set_color(0, 0, 0)
                ranger._set_color(0, 0, 0)
        # ----------------------------------

        if abs(lc) >= abs(Cl) and abs(rc) >= abs(Cr):
            break
            
        sleep(0.001)

    stop_all()

# -------------------------------------
# Distances & Angles
# -------------------------------------
D1 = 0.75                     
D2 = 0.50                     
D3 = 0.50                     
D4 = math.sqrt((0.75 - 0.50)**2 + 0.5**2)

TURN1 = math.radians(70)        
TURN2 = math.radians(-225)       
TURN3 = math.radians(57)
TURN4 = math.radians(90)

# -------------------------------------
# Main Execution
# -------------------------------------
print("System Ready. Ensure HRI and Ranger are connected.")

# 1. Visual Countdown
visual_countdown(5)

# 2. Straight (Blue/Magenta Strobe)
drive_straight(D1)
sleep(1)

# 3. Turn (Amber Blink)
spin(TURN1)
sleep(1)

# 4. Straight
drive_straight(D2)
sleep(1)

# 5. Turn
spin(TURN2)
sleep(1)

# 6. Straight
drive_straight(D3)
sleep(1)

# 7. Turn
spin(TURN3)
sleep(1)

# 8. Straight
drive_straight(D4)
sleep(1)

# Straighten Out
spin(TURN4)
sleep(1)

stop_all()
STBY.off()

print("Trail complete.")




