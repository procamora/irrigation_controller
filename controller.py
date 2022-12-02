#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from dataclasses import dataclass
from typing import Dict, Text, NoReturn, Tuple
import sys

from procamora_utils.logger import get_logging, logging

from ha import get_irrigation_ha, set_irrigation_ha

if sys.platform == 'darwin':
    log: logging = get_logging(verbose=True, name='gpio')
else:  # raspberry
    log: logging = get_logging(verbose=False, name='gpio')

try:
    import RPi.GPIO as GPIO

    GPIO.setwarnings(False)
except RuntimeError:
    log.critical("Error importing RPi.GPIO!  This is probably because you need superuser privileges.\n"
                 "You can achieve this by using 'sudo' to run your script")


# pinout  # bash
# sudo raspi-gpio get
# gpio readall  # bash  # gpio: command not found


@dataclass
class Controller:
    name_vegetable: Text = "Vegetable 🍅"
    name_front: Text = "Front Garden 🌴"
    name_back: Text = "Back Garden 🌵"
    pin_vegetable: int = 10
    pin_front: int = 12
    pin_back: int = 11

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

    def is_any_active(self) -> Tuple[bool, Dict]:
        status: Dict = self.get_status()
        return True in status.values(), status

    def set_pin_zone(self, zone: int, state: bool = False, name: Text = '') -> NoReturn:
        if zone == 0:
            pin: int = self.get_name_to_pin(name)
            log.debug(f'zone: {zone}, name: {name}, pin:{pin}, state:{state}')
            re.search('', name, re.IGNORECASE)
            GPIO.output(pin, state)
            clean_name: Text = re.sub(r'\W+', '', name)
        else:
            GPIO.output(zone, state)
            clean_name: Text = re.sub(r'\W+', '', self.get_pin_to_name(zone))

        if state == 'off' and not self.is_any_active():
            response = set_irrigation_ha(state='on' if state else 'off', entity="input_boolean.irrigation")
            log.debug(response)

        entity = f"input_boolean.irrigation_{clean_name}".lower()
        response = set_irrigation_ha(state='on' if state else 'off', entity=entity)
        log.debug(response)

    def get_name_to_pin(self, name: Text) -> int:
        if name == self.name_vegetable \
                or re.sub(r'\W+', '', name).lower() == re.sub(r'\W+', '', self.name_vegetable).lower():
            return self.pin_vegetable
        elif name == self.name_front \
                or re.sub(r'\W+', '', name).lower() == re.sub(r'\W+', '', self.name_front).lower():
            return self.pin_front
        elif name == self.name_back \
                or re.sub(r'\W+', '', name).lower() == re.sub(r'\W+', '', self.name_back).lower():
            return self.pin_back

    def get_pin_to_name(self, pin: int) -> Text:
        if pin == self.pin_vegetable:
            return self.name_vegetable
        elif pin == self.pin_front:
            return self.name_front
        elif pin == self.pin_back:
            return self.name_back

    def stop_all(self) -> NoReturn:
        for zone in [self.pin_vegetable, self.pin_front, self.pin_back]:
            self.set_pin_zone(zone, False)

    @staticmethod
    def cleanup() -> NoReturn:
        GPIO.cleanup()


def main():
    controller: Controller = Controller()
    log.debug(controller.get_status())
    controller.set_pin_zone(controller.pin_vegetable, True)
    log.debug(controller.get_status())
    controller.stop_all()
    log.debug(controller.get_status())


if __name__ == '__main__':
    main()
