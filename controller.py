#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Dict, Text, NoReturn

import RPi.GPIO as GPIO


# GPIO.setwarnings(False)

@dataclass
class Controller:
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

    def cleanup(self):
        GPIO.cleanup()