#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from datetime import datetime
from pathlib import Path
from typing import Dict
import sys

from procamora_utils.logger import get_logging, logging
from telebot import TeleBot

from controller import Controller

if sys.platform == 'darwin':
    log: logging = get_logging(verbose=True, name='watchdog')
else:  # raspberry
    log: logging = get_logging(verbose=False, name='watchdog')


def main():
    now: datetime = datetime.now()
    controller: Controller = Controller()

    any_active: bool
    status: Dict
    any_active, status = controller.is_any_active()
    if any_active:
        disable_notification = True
        if now.hour == 5 or now.hour == 6 or now.hour == 7 or now.hour == 8:
            disable_notification = False
        try:
            config: configparser.ConfigParser = configparser.ConfigParser()
            config.read(Path(Path(__file__).resolve().parent, "settings.cfg"))
            notifications: configparser.SectionProxy = config["NOTIFICATIONS"]

            bot: TeleBot = TeleBot(notifications.get('BOT_TOKEN'))
            bot.send_message(int(notifications.get('ADMIN')), f'watchdog => {status}',
                             disable_notification=disable_notification)
        except Exception as err:
            log.critical(f'Error: {err}')


if __name__ == '__main__':
    main()
