#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Dict, Text, NoReturn

from procamora_utils.logger import get_logging, logging

log: logging = get_logging(False, 'gpio')

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    log.critical("Error importing RPi.GPIO!  This is probably because you need superuser privileges.\n"
                 "You can achieve this by using 'sudo' to run your script")


# gpio readall  # bash
# GPIO.setwarnings(False)

@dataclass
class Controller:
    name_vegetable: Text = "Vegetable 🍅"
    name_front: Text = "Front Garden 🌴"
    name_back: Text = "Back Garden 🌵"
    zone_vegetable: int = 10
    zone_front: int = 11
    zone_back: int = 12

    def __post_init__(self):
        print(GPIO.RPI_INFO)
        GPIO.setmode(GPIO.BOARD)  # numeración exterior de los pines
        # self.gpio.setmode(gpio.BCM)  # numeración del chip BROADCOM
        GPIO.setup([self.zone_vegetable, self.zone_front, self.zone_back], GPIO.OUT, initial=GPIO.LOW)

    def get_status(self) -> Dict[Text, bool]:
        return {
            'vegetable': self.is_active(self.zone_vegetable),
            'front': self.is_active(self.zone_front),
            'back': self.is_active(self.zone_back),
        }

    def is_active(self, zone: int) -> bool:
        return GPIO.input(zone)

    def set_zone(self, zone: int, state: bool = False) -> NoReturn:
        GPIO.output(zone, state)

    def stop_all(self) -> NoReturn:
        for zone in [self.zone_vegetable, self.zone_front, self.zone_back]:
            self.set_zone(zone, False)

    def cleanup(self) -> NoReturn:
        GPIO.cleanup()


def main():
    controller: Controller = Controller()
    log.info(controller.get_status())
    log.info(controller.set_zone(controller.zone_vegetable, True))
    log.info(controller.get_status())
    log.info(controller.stop_all())
    log.info(controller.get_status())


if __name__ == '__main__':
    main()
