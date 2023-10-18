#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import configparser
# import re
import sys
from pathlib import Path
from typing import Text

from procamora_utils.logger import get_logging, logging
from telebot import TeleBot

from controller import Controller

# from ha import get_irrigation_ha, set_irrigation_ha

if sys.platform == 'darwin':
    log: logging = get_logging(verbose=True, name='cli')
else:  # raspberry
    log: logging = get_logging(verbose=False, name='cli')


def create_arg_parser() -> argparse:
    example = "python3 %(prog)s -e switch.irrigation_vegetable -s off"

    my_parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description='%(prog)s is a script to modify GPIO entity using HomeAssistant',
        usage=f'{example}')

    required_named = my_parser.add_argument_group('required named arguments')
    required_named.add_argument('-e', '--entity', help='The entity to modify', type=str, required=False)
    required_named.add_argument('-f', '--friendly_name', help='The friendly_name to modify', type=str, required=False)
    # required_named.add_argument('-s', '--state', help='entity status', action=argparse.BooleanOptionalAction)  # python 3.9
    required_named.add_argument('-s', '--state', type=str, help='Active entity', default='off')
    required_named.add_argument('-n', '--notify', action='store_true', help='Telegram Notification', default=True)
    # Python < 3.9:
    required_named.add_argument('-nn', '--no-notify', action='store_false', help='Telegram Notification', dest='notify')
    my_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose flag (boolean).', default=False)

    arg = my_parser.parse_args()
    if arg.friendly_name is None and arg.entity is None:
        my_parser.print_help()
        sys.exit(0)
    return arg


def main():
    arg = create_arg_parser()
    log.debug(arg)
    controller: Controller = Controller()

    entity_id: Text
    if arg.entity is None:
        entity_id = controller.get_entity_id(arg.friendly_name)
    else:
        entity_id = arg.entity

    log.debug(f'{entity_id} => {arg.state}')

    log.debug(controller.get_status())
    # set_irrigation_ha(state='on' if arg.state else 'off')
    controller.set_state(entity_id, arg.state)
    log.debug(controller.get_status())
    if arg.notify:
        try:
            config: configparser.ConfigParser = configparser.ConfigParser()
            config.read(Path(Path(__file__).resolve().parent, "settings.cfg"))

            notifications: configparser.SectionProxy = config["NOTIFICATIONS"]
            bot: TeleBot = TeleBot(notifications.get('BOT_TOKEN'))
            bot.send_message(int(notifications.get('GROUP')), f'{arg.friendly_name}({entity_id}) => {arg.state}',
                             disable_notification=True,
                             message_thread_id=int(notifications.get('TOPIC')))
        except Exception as err:
            log.critical(f'[-] Notify: {err}')


if __name__ == '__main__':
    main()
