import time
import lgpio
import threading
import logging

from smbus2 import SMBus

logger = logging.getLogger(__name__)

IODIRA = 0x00
IODIRB = 0x01
IPOLA = 0x02
IPOLB = 0x03
GPINTENA = 0x04
GPINTENB = 0x05
DEFVALA = 0x06
DEFVALB = 0x07
INTCONA = 0x08
INTCONB = 0x09
IOCON = 0x0A
GPPUA = 0x0C
GPPUB = 0x0D
INTFA = 0x0E
INTFB = 0x0F
INTCAPA = 0x10
INTCAPB = 0x11
GPIOA = 0x12
GPIOB = 0x13

SMBUS_NUMBER = 1
I2C_ADDRESS = 0x20
INTERRUPT_PIN = 23

class GpioMCP23017:
    def __init__(self, address=I2C_ADDRESS, bus_number=SMBUS_NUMBER, interrupt_pin=INTERRUPT_PIN):
        self.bus = SMBus(bus_number)
        self.address = address
        self.interrupt_pin = interrupt_pin
        self.button_names = {}
        self.encoders = {}
        self.callbacks = {}
        self.button_press_times = {}
        self.long_press_triggered = {}
        self.long_press_threshold = 1.0
        self.timer = None
        self.gpio_handle = lgpio.gpiochip_open(0)

        # Configure MCP23017
        self.bus.write_byte_data(self.address, IODIRA, 0xFF)
        self.bus.write_byte_data(self.address, GPPUA, 0xFF)
        self.bus.write_byte_data(self.address, IODIRB, 0xFF)
        self.bus.write_byte_data(self.address, GPPUB, 0xFF)

        # Configure interrupts on MCP23017
        # IOCON: Mirror interrupts, Active-HIGH (bit 1 = 1), Open-drain disabled
        # Try active-high configuration: 0b01000010
        self.bus.write_byte_data(self.address, IOCON, 0b01000010)

        # Enable interrupt-on-change for all pins
        self.bus.write_byte_data(self.address, GPINTENA, 0xFF)
        self.bus.write_byte_data(self.address, GPINTENB, 0xFF)

        self.last_state_a = self.bus.read_byte_data(self.address, GPIOA)
        self.bus.read_byte_data(self.address, GPIOB)

        # Setup GPIO interrupt - use BOTH edges to catch the signal
        lgpio.gpio_claim_input(
            self.gpio_handle, self.interrupt_pin, lgpio.SET_PULL_DOWN
        )

        # Set alert for RISING edge (LOW to HIGH) since that's what we're seeing
        lgpio.gpio_claim_alert(
            self.gpio_handle,
            self.interrupt_pin,
            lgpio.RISING_EDGE,  
        )

        self.callback_id = lgpio.callback(
            self.gpio_handle,
            self.interrupt_pin,
            lgpio.RISING_EDGE, 
            self._interrupt_handler,
        )

        logger.debug(f"GPIO {self.interrupt_pin} configured for RISING edge interrupts")

    def _interrupt_handler(self, chip, gpio, level, tick):
        """Called when MCP23017 triggers interrupt"""
        self.check_presses()
        self.check_encoders()

        # Clear interrupt by reading GPIO registers
        self.bus.read_byte_data(self.address, GPIOA)
        self.bus.read_byte_data(self.address, GPIOB)

    def add_button(self, name, pin_number, callback=None, long_press_callback=None):
        self.button_names[pin_number] = name
        if callback:
            self.callbacks[("button", name)] = callback
        if long_press_callback:
            self.callbacks[("long_press", name)] = long_press_callback

    def add_encoder(self, name, clk_pin, dt_pin, callback=None):
        port_b = self.read_port_b()
        clk = (port_b >> clk_pin) & 1
        dt = (port_b >> dt_pin) & 1

        self.encoders[name] = {
            "clk": clk_pin,
            "dt": dt_pin,
            "prev_state": (clk << 1) | dt,
            "store": 0,
        }
        if callback:
            self.callbacks[("encoder", name)] = callback

    def read_buttons(self):
        return self.bus.read_byte_data(self.address, GPIOA)

    def read_port_b(self):
        return self.bus.read_byte_data(self.address, GPIOB)

    def check_presses(self):
        current_state = self.read_buttons()

        for pin in range(8):
            mask = 1 << pin
            was_pressed = not (self.last_state_a & mask)
            is_pressed = not (current_state & mask)

            if pin in self.button_names:
                name = self.button_names[pin]

                if is_pressed and not was_pressed:
                    self.button_press_times[pin] = time.time()
                    self.long_press_triggered[pin] = False

                    self._schedule_long_press_check(pin, name)

                elif not is_pressed and was_pressed:
                    if pin in self.button_press_times:
                        if not self.long_press_triggered.get(pin, False):
                            if ("button", name) in self.callbacks:
                                self.callbacks[("button", name)]()

                        del self.button_press_times[pin]
                        self.long_press_triggered.pop(pin, None)

        self.last_state_a = current_state

    def _schedule_long_press_check(self, pin, name):
        """Schedule a check after threshold time"""

        def check():
            current_state = self.read_buttons()
            mask = 1 << pin
            is_still_pressed = not (current_state & mask)

            if is_still_pressed and pin in self.button_press_times:
                if ("long_press", name) in self.callbacks:
                    self.callbacks[("long_press", name)]()
                self.long_press_triggered[pin] = True

        threading.Timer(self.long_press_threshold, check).start()

    def close(self):
        if hasattr(self, "callback_id"):
            self.callback_id.cancel()

        if hasattr(self, "gpio_handle"):
            lgpio.gpio_free(self.gpio_handle, self.interrupt_pin)
            lgpio.gpiochip_close(self.gpio_handle)

        self.bus.close()

    def check_encoders(self):
        port_b_state = self.read_port_b()

        for name, encoder in self.encoders.items():
            clk_pin = encoder["clk"]
            dt_pin = encoder["dt"]

            clk = (port_b_state >> clk_pin) & 1
            dt = (port_b_state >> dt_pin) & 1

            current_state = (clk << 1) | dt
            prev_state = encoder["prev_state"]

            if current_state != prev_state:
                if prev_state == 0b11:
                    if current_state == 0b01:
                        encoder["store"] += 1
                    elif current_state == 0b10:
                        encoder["store"] -= 1
                elif prev_state == 0b01:
                    if current_state == 0b00:
                        encoder["store"] += 1
                    elif current_state == 0b11:
                        encoder["store"] -= 1
                elif prev_state == 0b00:
                    if current_state == 0b10:
                        encoder["store"] += 1
                    elif current_state == 0b01:
                        encoder["store"] -= 1
                elif prev_state == 0b10:
                    if current_state == 0b11:
                        encoder["store"] += 1
                    elif current_state == 0b00:
                        encoder["store"] -= 1

                encoder["prev_state"] = current_state

                if encoder["store"] >= 4:
                    direction = "CW"
                    encoder["store"] = 0
                    if ("encoder", name) in self.callbacks:
                        self.callbacks[("encoder", name)](direction)

                elif encoder["store"] <= -4:
                    direction = "CCW"
                    encoder["store"] = 0
                    if ("encoder", name) in self.callbacks:
                        self.callbacks[("encoder", name)](direction)

    def is_pressed(self, pin_number):
        state = self.read_buttons()
        return not (state & (1 << pin_number))

    def close(self):
        if hasattr(self, "callback_id"):
            self.callback_id.cancel()

        if hasattr(self, "gpio_handle"):
            lgpio.gpio_free(self.gpio_handle, self.interrupt_pin)
            lgpio.gpiochip_close(self.gpio_handle)

        self.bus.close()
