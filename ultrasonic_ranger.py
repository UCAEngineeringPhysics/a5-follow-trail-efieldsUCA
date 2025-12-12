# File: ultrasonic_ranger.py
from machine import Pin
import utime

class UltrasonicRanger:
    def __init__(self, trig_id, echo_id, led_ids: tuple):
        self.trig_pin = Pin(trig_id, Pin.OUT)
        self.echo_pin = Pin(echo_id, Pin.IN, Pin.PULL_DOWN)
        
        self.led_red = Pin(led_ids[0], Pin.OUT)
        self.led_green = Pin(led_ids[1], Pin.OUT)
        self.led_blue = Pin(led_ids[2], Pin.OUT)
        
        self.distance_m = None
        self._echo_start_us = 0
        self.last_trigger_ms = 0
        
        self.echo_pin.irq(handler=self._echo_handler, trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING)
        print("Ultrasonic Ranger initialized.")

    def _echo_handler(self, pin):
        if pin.value() == 1:
            self._echo_start_us = utime.ticks_us()
        else:
            if self._echo_start_us == 0: return
            duration_us = utime.ticks_diff(utime.ticks_us(), self._echo_start_us)
            if 100 < duration_us < 38000:
                self.distance_m = (duration_us / 58) / 100
            else:
                self.distance_m = None

    def _set_color(self, r=0, g=0, b=0):
        self.led_red.value(r)
        self.led_green.value(g)
        self.led_blue.value(b)
    
    def get_distance_cm(self):
        dist_m = self.distance_m
        return dist_m * 100 if dist_m is not None else -1.0

    def update(self):
        if utime.ticks_diff(utime.ticks_ms(), self.last_trigger_ms) > 100:
            self.last_trigger_ms = utime.ticks_ms()
            self.trig_pin.on()
            utime.sleep_us(10)
            self.trig_pin.off()

        dist_cm = self.get_distance_cm()
        if dist_cm < 0: self._set_color(0,0,0)
        elif dist_cm < 10: self._set_color(r=1, g=0, b=0)
        elif dist_cm < 20: self._set_color(r=1, g=1, b=0)
        elif dist_cm < 40: self._set_color(r=0, g=1, b=0)
        elif dist_cm < 60: self._set_color(r=0, g=1, b=1)
        elif dist_cm < 100: self._set_color(r=0, g=0, b=1)
        else: self._set_color(r=1, g=0, b=1)