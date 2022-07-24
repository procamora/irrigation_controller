#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Dict, Text, NoReturn

from procamora_utils.logger import get_logging, logging

log: logging = get_logging(True, 'gpio')


@dataclass
class GPIO_FAKE:
    RPI_INFO = ''
    BOARD = ''
    OUT = ''
    IN = ''
    LOW = ''
    HIGH = ''

    def setmode(self, asd):
        pass

    def setwarnings(self, asd):
        pass

    def setup(self, a, b):
        pass

    def input(self, a):
        return True

    def output(self, a, b):
        pass

    def cleanup(self):
        pass


try:
    import RPi.GPIO as GPIO
except RuntimeError:
    log.critical("Error importing RPi.GPIO!  This is probably because you need superuser privileges.\n"
                 "You can achieve this by using 'sudo' to run your script")
except ModuleNotFoundError:  # FIXME Debug
    GPIO = GPIO_FAKE()


# pinout  # bash
# sudo raspi-gpio get
# gpio readall  # bash  # gpio: command not found
# GPIO.setwarnings(False)

@dataclass
class Controller:
    name_vegetable: Text = "Vegetable 🍅"
    name_front: Text = "Front Garden 🌴"
    name_back: Text = "Back Garden 🌵"
    pin_vegetable: int = 10
    pin_front: int = 11
    pin_back: int = 12

    def __post_init__(self):
        print(GPIO.RPI_INFO)
        # GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)  # numeración exterior de los pines (11)
        # self.gpio.setmode(gpio.BCM)  # numeración del chip BROADCOM (GPIO17)
        # initial no se puede poner, porque si no cada vez que se instancia controller se ponen todos a false
        # GPIO.setup([self.pin_vegetable, self.pin_front, self.pin_back], GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup([self.pin_vegetable, self.pin_front, self.pin_back], GPIO.OUT)

    def get_status(self) -> Dict[Text, bool]:
        return {
            self.name_vegetable: self.is_active(self.pin_vegetable),
            self.name_front: self.is_active(self.pin_front),
            self.name_back: self.is_active(self.pin_back),
        }

    @staticmethod
    def is_active(zone: int) -> bool:
        return GPIO.input(zone)

    def set_pin_zone(self, zone: int, state: bool = False, name: Text = '') -> NoReturn:
        if zone == 0:
            pin: int = self.get_pin_zone(name)
            log.debug(f'zone: {zone}, name: {name}, pin:{pin}, state:{state}')
            GPIO.output(pin, state)
        else:
            GPIO.output(zone, state)

    def get_pin_zone(self, name: Text) -> int:
        if name == self.name_vegetable:
            return self.pin_vegetable
        elif name == self.name_front:
            return self.pin_front
        elif name == self.name_back:
            return self.pin_back

    def stop_all(self) -> NoReturn:
        for zone in [self.pin_vegetable, self.pin_front, self.pin_back]:
            self.set_pin_zone(zone, False)

    @staticmethod
    def cleanup() -> NoReturn:
        GPIO.cleanup()


def main():
    controller: Controller = Controller()
    log.info(controller.get_status())
    controller.set_pin_zone(controller.pin_vegetable, True)
    log.info(controller.get_status())
    controller.stop_all()
    log.info(controller.get_status())


if __name__ == '__main__':
    main()
