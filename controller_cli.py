#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import configparser
import re
import sys
from pathlib import Path

from procamora_utils.logger import get_logging, logging
from telebot import TeleBot

from controller import Controller

log: logging = get_logging(True, 'gpio')


def create_arg_parser() -> argparse:
    example = "python3 %(prog)s -p 10 -a -v"

    my_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='%(prog)s is a script to modify GPIO pin',
        usage=f'{example}')

    required_named = my_parser.add_argument_group('required named arguments')
    required_named.add_argument('-p', '--pin', help='The pin to modify', type=int, required=False)
    required_named.add_argument('-z', '--zone', help='The zone to modify', type=str, required=False)
    # required_named.add_argument('-a', '--active', help='Pin status', action=argparse.BooleanOptionalAction)  # python 3.9
    required_named.add_argument('-a', '--active', action='store_true', help='Active Pin', default=False)  # Python < 3.9:
    required_named.add_argument('-na', '--no-active', action='store_false', help='-Desactivate Pin', dest='active')
    required_named.add_argument('-n', '--notify', action='store_true', help='Telegram Notification', default=True)  # Python < 3.9:
    required_named.add_argument('-nn', '--no-notify', action='store_false', help='Telegram Notification', dest='notify')
    my_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose flag (boolean).', default=False)

    arg = my_parser.parse_args()
    if arg.zone is None and arg.pin is None:
        my_parser.print_help()
        sys.exit(0)
    return arg


def main():
    arg = create_arg_parser()
    log.info(arg)
    controller: Controller = Controller()

    pin: int
    if arg.zone is not None:
        if re.search(arg.zone, controller.name_vegetable, re.IGNORECASE):
            pin = controller.pin_vegetable
        elif re.search(arg.zone, controller.name_front, re.IGNORECASE):
            pin = controller.pin_front
        elif re.search(arg.zone, controller.name_back, re.IGNORECASE):
            pin = controller.pin_back
        else:
            log.critical(f'{arg.zone} not regex')
            sys.exit(1)
    else:
        pin = arg.pin

    log.info(f'{pin} => {arg.active}')

    log.info(controller.get_status())
    controller.set_pin_zone(pin, arg.active)
    log.info(controller.get_status())
    if arg.notify:
        try:
            config: configparser.ConfigParser = configparser.ConfigParser()
            config.read(Path(Path(__file__).resolve().parent, "settings.cfg"))
            notifications: configparser.SectionProxy = config["NOTIFICATIONS"]

            bot: TeleBot = TeleBot(notifications.get('BOT_TOKEN'))
            bot.send_message(int(notifications.get('ADMIN')), f'{arg.zone}({pin}) => {arg.active}', disable_notification=True)
        except Exception as err:
            log.critical(f'Error: {err}')


if __name__ == '__main__':
    main()
