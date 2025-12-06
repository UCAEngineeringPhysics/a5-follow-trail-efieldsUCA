# File: hri_controller.py
from machine import Pin, PWM, reset
import utime

class HRIController:
    def __init__(self, button_id, led_ids: tuple):
        self.button = Pin(button_id, Pin.IN, Pin.PULL_DOWN)
        self.red = PWM(Pin(led_ids[0]))
        self.green = PWM(Pin(led_ids[1]))
        self.blue = PWM(Pin(led_ids[2]))
        for p in (self.red, self.green, self.blue):
            p.freq(1000)
            p.duty_u16(0)
            
        self.MODE_PAUSE, self.MODE_WORK = 0, 1
        self.mode = self.MODE_PAUSE
        self.work_time_ms = 0
        self.work_enter_ms = None
        self.last_press_state = self.button.value()
        self.button_press_ms = None
        self.red_blink_enable_ms = None

        self.GREEN_TO_BLUE_S = 45
        self.RED_BLINK_START_S = 55
        self.RED_BLINK_INTERRUPT_S = 5
        self.HARD_RESET_S = 3
        print("HRI Controller initialized.")
        
    def _set_color(self, r, g, b):
        self.red.duty_u16(int(r))
        self.green.duty_u16(int(g))
        self.blue.duty_u16(int(b))

    def get_mode_str(self):
        return "Work" if self.mode == self.MODE_WORK else "Pause"

    def toggle_mode(self):
        now_ms = utime.ticks_ms()
        if self.mode == self.MODE_WORK:
            if self.work_enter_ms is not None:
                self.work_time_ms += utime.ticks_diff(now_ms, self.work_enter_ms)
            self.work_enter_ms = None
            self.mode = self.MODE_PAUSE
        else:
            self.work_enter_ms = now_ms
            self.mode = self.MODE_WORK
            
    def get_total_work_seconds(self):
        # This is the function that was missing
        total_work_ms = self.work_time_ms
        if self.mode == self.MODE_WORK and self.work_enter_ms is not None:
            total_work_ms += utime.ticks_diff(utime.ticks_ms(), self.work_enter_ms)
        return total_work_ms / 1000.0

    def update(self):
        now_ms = utime.ticks_ms()
        raw_button = self.button.value()
        if raw_button != self.last_press_state:
            self.last_press_state = raw_button
            if raw_button == 1:
                self.button_press_ms = now_ms
                self.toggle_mode()
            else:
                self.button_press_ms = None
        
        if self.button.value() == 1 and self.button_press_ms is not None:
            if utime.ticks_diff(now_ms, self.button_press_ms) >= self.HARD_RESET_S * 1000:
                reset()
                
        total_work_s = self.get_total_work_seconds()

        base_r, base_g, base_b = (0, 65535, 0)
        if total_work_s >= self.GREEN_TO_BLUE_S:
            base_r, base_g, base_b = (0, 0, 65535)
        
        if self.mode == self.MODE_PAUSE:
            # 1Hz fade (1000ms cycle)
            phase = utime.ticks_diff(now_ms, 0) % 1000
            bright = abs(phase - 500) / 500
            r, g, b = int(base_r * bright), int(base_g * bright), int(base_b * bright)
        else:
            r, g, b = base_r, base_g, base_b
            
        if total_work_s >= self.RED_BLINK_START_S:
            if self.red_blink_enable_ms is None:
                self.red_blink_enable_ms = now_ms
            
            # 10Hz blink (50ms on, 50ms off)
            if (utime.ticks_diff(now_ms, 0) // 50) % 2 == 0:
                r, g, b = 65535, 0, 0 # Only RED is on
            else:
                r, g, b = 0, 0, 0 # Fully off
                
            if utime.ticks_diff(now_ms, self.red_blink_enable_ms) >= self.RED_BLINK_INTERRUPT_S * 1000:
                reset()
        else:
            self.red_blink_enable_ms = None
        
        self._set_color(r, g, b)