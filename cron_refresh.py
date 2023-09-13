#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import configparser
# import re
import sys
from pathlib import Path
from typing import Text, Optional

from telebot import TeleBot, types, apihelper
from procamora_utils.logger import get_logging, logging

from cron import Cron
from gcalendar import GCalendar

if sys.platform == 'darwin':
    log: logging = get_logging(verbose=True, name='cli')
else:  # raspberry
    log: logging = get_logging(verbose=False, name='cli')


def get_events(calendar: GCalendar, calendar_id: Text, file_cron: Path, num_events: int, bot: Optional[TeleBot],
               id_admin: Optional[int]) -> Optional[Text]:
    cron: Cron = calendar.get_irrigation(calendar_id, num_events)
    if cron is not None:
        write: bool
        stdout: Text
        stderr: Text
        write, stdout, stderr = cron.write(file_cron)  # Permiso admin para escribir
        if write:
            if len(stderr) != 0:
                msg_err: Text = f'[+] stderr: {stderr}'
                log.error(msg_err)
                if bot is None:
                    return msg_err
                else:
                    bot.send_message(id_admin, msg_err, disable_notification=False)
            if len(stdout) != 0:
                msg_err: Text = f'[+] stdout: {stdout}'
                if bot is None:
                    return msg_err
                else:
                    bot.send_message(id_admin, msg_err, disable_notification=False)


def main():
    try:
        config: configparser.ConfigParser = configparser.ConfigParser()
        config.read(Path(Path(__file__).resolve().parent, "settings.cfg"))
        config_basic: configparser.SectionProxy = config["BASICS"]
        calendar_id: Text = config_basic.get('CALENDAR_ID')
        file_cron: Path = Path(config_basic.get('FILE_CRON'))
        num_events: int = int(config_basic.get('NUM_EVENTS'))
        id_admin: int = int(config["NOTIFICATIONS"]["ADMIN"])

        bot: TeleBot = TeleBot(config["NOTIFICATIONS"]["BOT_TOKEN"])
        get_events(GCalendar(), calendar_id, file_cron, num_events, bot, id_admin)
    except Exception as err:
        log.critical(f'[-] Notify: {err}')


if __name__ == "__main__":
    main()
