#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from datetime import datetime
from pathlib import Path
from typing import Dict
import sys
import re

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
    log.debug(f'{any_active} => {status} hour({now.hour})')
    if any_active:
        disable_notification = False
        if 5 <= now.hour <= 7 or 14 <= now.hour <= 15:
            disable_notification = True
        try:
            config: configparser.ConfigParser = configparser.ConfigParser()
            config.read(Path(Path(__file__).resolve().parent, "settings.cfg"))
            notifications: configparser.SectionProxy = config["NOTIFICATIONS"]

            filter_status = list(filter(lambda e: e[1] == 'on', status.items()))
            status_clean = list(map(lambda i: re.sub('irrigation ', '', i[0], flags=re.IGNORECASE), filter_status))

            if disable_notification:  # to reduce the number of notifications
                return

            bot: TeleBot = TeleBot(notifications.get('BOT_TOKEN'))
            bot.send_message(int(notifications.get('GROUP')), f'‼️ WATCHDOG => {status_clean} ‼️',
                             disable_notification=disable_notification)
        except Exception as err:
            log.critical(f'Error: {err}')


if __name__ == '__main__':
    main()
