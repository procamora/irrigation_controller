#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# https://geekytheory.com/telegram-programando-un-bot-en-python/
# https://bitbucket.org/master_groosha/telegram-proxy-bot/src/07a6b57372603acae7bdb78f771be132d063b899/proxy_bot.py?at=master&fileviewer=file-view-default
# https://github.com/eternnoir/pyTelegramBotAPI/blob/master/telebot/types.py


import configparser
import json
import os
import re
import signal
import sys
import threading
import time
from pathlib import Path
from typing import NoReturn, Tuple, Text, List, Dict
import requests
import psutil

from procamora_utils.logger import get_logging, logging
from requests import exceptions
from telebot import TeleBot, types, apihelper
from terminaltables import AsciiTable

from cron import Cron
from gcalendar import GCalendar
from controller import Controller
from cron_refresh import get_events

if sys.platform == 'darwin':
    log: logging = get_logging(verbose=True, name='bot_irrigation')
else:  # raspberry
    log: logging = get_logging(verbose=False, name='bot_irrigation')

controller: Controller = Controller()


def get_basic_file_config():
    return '''[BASICS]
ADMIN = 111111
BOT_TOKEN = 1069111113:AAHOk9K5TAAAAAAAAAAIY1OgA_LNpAAAAA
DEBUG = 0
DELAY = 300
CALENDAR_ID = sdfdsfsdf@group.calendar.google.com
NUM_EVENTS = 30
FILE_CRON = /etc/cron.d/irrigation

[NOTIFICATIONS]
ADMIN = 111111
GROUP = -111111111111
TOPIC_IRRIGATION_ID = 234234
BOT_TOKEN = 1069111113:AAHOk9K5TAAAAAAAAAAIY1OgA_LNpAAAAA

[DEBUG]
ADMIN = 111111
BOT_TOKEN = 1069111113:AAHOk9K5TAAAAAAAAAAIY1OgA_LNpAAAAA
'''


my_commands: Tuple[Text, ...] = (
    '/status',  # 0
    '/get',  # 1
    '/set',  # 2
    '/off',  # 3
    '/refresh',  # 4
    '/events',  # 5
    '/help'  # -2
    '/exit',  # -1
)

FILE_CONFIG: Path = Path(Path(__file__).resolve().parent, "settings.cfg")
if not FILE_CONFIG.exists():
    log.critical(f'File {FILE_CONFIG} not exists and is necesary')
    FILE_CONFIG.write_text(get_basic_file_config())
    log.critical(f'Creating file {FILE_CONFIG}. It is necessary to configure the file.')
    sys.exit(1)

config: configparser.ConfigParser = configparser.ConfigParser()
config.read(FILE_CONFIG)

config_basic: configparser.SectionProxy = config["BASICS"]

if bool(int(config_basic.get('DEBUG'))):
    bot: TeleBot = TeleBot(config["DEBUG"].get('BOT_TOKEN'))
else:
    bot: TeleBot = TeleBot(config_basic.get('BOT_TOKEN'))

owner_bot: List = list(map(lambda i: int(i), config_basic.get('ADMIN').split(',')))
log.info(owner_bot)
topic_bot = int(config_basic.get('TOPIC'))
calendar_id: Text = config_basic.get('CALENDAR_ID')
file_cron: Path = Path(config_basic.get('FILE_CRON'))


def get_markup_cmd() -> types.ReplyKeyboardMarkup:
    markup: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row(my_commands[0])
    markup.row(my_commands[1], my_commands[2], my_commands[3])
    markup.row(my_commands[4], my_commands[5])
    return markup


def get_markup_zones() -> types.ReplyKeyboardMarkup:
    markup: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row(controller.back_left['name'], controller.back_right['name'])
    markup.row(controller.front['name'], controller.vegetable['name'])
    return markup


def get_markup_status() -> types.ReplyKeyboardMarkup:
    markup: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row("ON", "OFF")
    # markup.row(my_commands[4])
    return markup


# def get_markup_zones2() -> types.ReplyKeyboardMarkup:
#     markup: types.ReplyKeyboardMarkup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
#     markup.row(controller.back_left['name'], controller.back_right['name'])
#     markup.row(controller.front['name'], controller.vegetable['name'])
#     # markup.row(my_commands[4])
#     return markup


# def get_markup_new_host(host: Any):
#     markup = InlineKeyboardMarkup()
#     inline_keyboard: Tuple[InlineKeyboardButton, ...] = (InlineKeyboardButton('nmap', callback_data=f'nmap_{host.ip}'),
#                                                          InlineKeyboardButton('openvas', callback_data=f'openvas_{host.ip}'),
#                                                          InlineKeyboardButton('description', callback_data=f'description_{host.mac}'))
#     markup.row_width = len(inline_keyboard)
#     markup.add(InlineKeyboardButton('nmap', callback_data=f'nmap_{host.ip}'),
#                InlineKeyboardButton('openvas', callback_data=f'openvas_{host.ip}'),
#                InlineKeyboardButton('description', callback_data=f'description_{host.mac}'))
#     return markup

def send_message_safe(message: types.Message, text: Text) -> NoReturn:
    if len(text) > 4096:
        new_msg = f'{str(text)[0:4050]}\n.................\nTruncated message'
        bot.reply_to(message, new_msg, reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
    else:
        bot.reply_to(message, text, reply_markup=get_markup_cmd(), message_thread_id=topic_bot)


# def report_and_repeat(message: types.Message, mac: Text, func: Callable, info: Text):
#     """
#     Metodo auxiliar con el que volver a preguntar tras una respuesta no valida
#     :param message:
#     :param protocol:
#     :param func:
#     :param info:
#     :return:
#     """
#     bot.reply_to(message, info, reply_markup=get_markup_cmd())
#     bot.register_next_step_handler(message, func, mac=mac)


def is_response_command(message: types.Message):
    response: bool = False
    if message.text[0] == '/':
        response = True

    if message.text == my_commands[-1]:  # exit
        bot.reply_to(message, "Cancelled the change of description", reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
    elif message.text == my_commands[-2]:  # help
        command_help(message)
    elif message.text == my_commands[0]:  # status
        send_status(message)
    elif message.text == my_commands[1]:  # get
        send_get(message)
    elif message.text == my_commands[2]:  # set
        send_set(message)
    elif message.text == my_commands[3]:  # off
        send_off(message)
    return response


# def check_description(message: types.Message, mac: Text) -> NoReturn:
#     if is_response_command(message):
#         return
#
#     if not re.search(r'^(\w+| )+$', message.text):
#         report_and_repeat(message, mac, check_description,
#                           'Enter a valid description, it can only contains alphanumeric characters and space')
#         return
#
#     # update_descriptions(mac, description=message.text, lock=lock)
#     bot.reply_to(message, 'update description', reply_markup=get_markup_cmd())


# @bot.callback_query_handler(func=lambda call: True)
# def callback_query(call: types.CallbackQuery):
#     ip: Text = call.data.split('_')[1]
#     if re.search(r'nmap_.*', call.data):
#         bot.answer_callback_query(call.id, f"run thread scan tcp nmap to {ip}")
#         d = threading.Thread(target=daemon_tcp_scan, name='tcp_scan', args=(ip, call.message))
#         d.setDaemon(True)
#         d.start()
#     elif re.search(r'openvas_.*', call.data):
#         bot.answer_callback_query(call.id, f"run thread scan tcp openvas to {ip}")
#         d = threading.Thread(target=daemon_openvas_scan, name='openvas_scan', args=(ip, call.message))
#         d.setDaemon(True)
#         d.start()
#     elif re.search(r'description_.*', call.data):
#         mac: Text = ip
#         bot.answer_callback_query(call.id, f"creating description for {mac}")
#         bot.reply_to(call.message, f'What description do you want to give to the host: {mac}', reply_markup=get_markup_cmd())
#         bot.register_next_step_handler(call.message, check_description, mac=mac)


# Handle always first "/start" message when new chat with your bot is created
@bot.message_handler(commands=["start"])
def command_start(message: types.Message) -> NoReturn:
    bot.send_message(message.chat.id, f"Welcome to the bot\nYour id is: {message.chat.id}",
                     reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
    command_system(message)
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(commands=["help"])
def command_help(message: types.Message) -> NoReturn:
    bot.send_message(message.chat.id, "Here I will put all the options", message_thread_id=topic_bot)
    markup = types.InlineKeyboardMarkup()
    itembtna = types.InlineKeyboardButton('Github', url="https://github.com/procamora/irrigation_controller")
    markup.row(itembtna)
    bot.send_message(message.chat.id, "Here I will put all the options",
                     reply_markup=markup, message_thread_id=topic_bot)
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(commands=["system"])
def command_system(message: types.Message) -> NoReturn:
    bot.send_message(message.chat.id, "List of available commands\nChoose an option: ",
                     reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
    return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(func=lambda message: message.chat.id in owner_bot, commands=[my_commands[-1][1:]])
def send_exit(message: types.Message) -> NoReturn:
    bot.send_message(message.chat.id, "Nothing", reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
    return


@bot.message_handler(func=lambda message: message.chat.id in owner_bot, commands=[my_commands[0][1:]])
def send_status(message: types.Message) -> NoReturn:
    response = list([['Zone', 'State']])
    zones = controller.get_status()
    log.debug(zones.items())
    for zone in zones.items():
        z = (zone[0].replace('Irrigation ', '').strip(), zone[1])
        response.append(z)

    table: AsciiTable = AsciiTable(response)
    table.justify_columns = {0: 'center', 1: 'center'}
    send_message_safe(message, str(table.table))
    return


@bot.message_handler(func=lambda message: message.chat.id in owner_bot, commands=[my_commands[1][1:]])
def send_get(message: types.Message) -> NoReturn:
    regex: re.Match = re.search(r'^/(?P<get>get)(@\w+)? (?P<zone>\w+)$',
                                str(message.text).strip(), re.IGNORECASE)
    if not regex:
        bot.reply_to(message, "get zone", reply_markup=get_markup_zones(), message_thread_id=topic_bot)
        bot.register_next_step_handler(message, update_pin, action='get')
    else:  # /get vegetable    or /get@domotica_pablo_bot vegetable
        message.text = regex.groupdict()['zone']
        update_pin(message=message, action='get')
    return


@bot.message_handler(func=lambda message: message.chat.id in owner_bot, commands=[my_commands[2][1:]])
def send_set(message: types.Message) -> NoReturn:
    regex: re.Match = re.search(r'^/(?P<set>set)(@\w+)? (?P<zone>\w+) (?P<action>ON|OFF)$',
                                str(message.text).strip(), re.IGNORECASE)
    if not regex:
        bot.reply_to(message, "set zone", reply_markup=get_markup_zones(), message_thread_id=topic_bot)
        bot.register_next_step_handler(message, set_status_zone, action='set')
    else:  # /set vegetable on  or /set@domotica_pablo_bot vegetable on
        message.text = regex.groupdict()['action']
        update_pin(message=message, action='set', other=regex.groupdict()['zone'])
    return


def set_status_zone(message: types.Message, action: Text) -> NoReturn:
    if is_response_command(message):
        return

    bot.reply_to(message, "set status", reply_markup=get_markup_status(), message_thread_id=topic_bot)
    bot.register_next_step_handler(message, update_pin, action=action, other=message.text)


def update_pin(message: types.Message, action: Text, other: Text = None) -> NoReturn:
    if is_response_command(message):
        return

    if action == 'get':
        entity_id: Text = controller.get_entity_id(message.text)
        status_zone: bool = controller.is_active(entity_id)
        bot.reply_to(message, f'get({message.text}) => {status_zone}',
                     reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
    elif action == 'set':
        controller.set_state(state=message.text.lower(), friendly_name=other)
        # set(OFF) => Vegetable 🍅
        bot.reply_to(message, f'set({message.text}) => {other}',
                     reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
        send_status(message)
    else:
        bot.reply_to(message, f'uknown action => {action}',
                     reply_markup=get_markup_cmd(), message_thread_id=topic_bot)


@bot.message_handler(func=lambda message: message.chat.id in owner_bot, commands=[my_commands[3][1:]])
def send_off(message: types.Message) -> NoReturn:
    send_status(message)
    bot.reply_to(message, "closed all relays", reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
    controller.stop_all()
    send_status(message)
    return


@bot.message_handler(func=lambda message: message.chat.id in owner_bot, commands=[my_commands[4][1:]])
def send_refresh(message: types.Message) -> NoReturn:
    try:
        log.debug('get calendar and update cron')
        get_events(GCalendar(), calendar_id, file_cron, int(config_basic.get('NUM_EVENTS')), bot=None, id_admin=None)
        bot.reply_to(message, "update calendars and cron", reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
        send_events(message)
    except Exception as err:
        log.error(f'[-] Error: {err}')
        bot.send_message(owner_bot[1], f'[-] Error GCalendar send_refresh: {err}',
                         reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
    return


@bot.message_handler(func=lambda message: message.chat.id in owner_bot, commands=[my_commands[5][1:]])
def send_events(message: types.Message) -> NoReturn:
    response: List[List[Text]] = list([['Zone', 'Date']])

    cron: Cron = Cron(user="")
    try:
        crons: List[List[Text]] = cron.cron_to_list(file_cron)
    except Exception as err:
        log.critical(f'[-] Error cron_to_list: {err}')
        bot.reply_to(message, f'[-] Error cron_to_list: {err}',
                     reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
        return

    log.debug(crons)
    if len(crons) == 0:
        bot.reply_to(message, f"no events in {str(file_cron)}",
                     reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
        return

    for zone in crons[0:20]:  # only 20 events, more maybe exceded limit message size
        response.append(zone)

    table: AsciiTable = AsciiTable(response)
    table.justify_columns = {0: 'center', 1: 'center'}
    send_message_safe(message, str(table.table))
    return


# @bot.message_handler(func=lambda message: message.chat.id in owner_bot, content_types=["document"])
# def my_document(message: types.Message) -> NoReturn:
#     if message.document.mime_type == 'application/json':
#         try:
#             file_info: types.File = bot.get_file(message.document.file_id)
#             # bot.send_message(message.chat.id, f'https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}')
#             file: requests.Response = requests.get(
#                 f'https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}')
#             torrent_file: Path = Path(Path(__file__).resolve().parent, 'credentials_aux.json')
#             torrent_file.write_bytes(file.content)
#         except Exception as err:
#             log.error(f'[-] Error: {err}')
#             bot.reply_to(message, f'[-] Error file json: {err}', reply_markup=get_markup_cmd())
#             return
#
#         try:
#             arr: Dict = json.loads(torrent_file.read_text())
#             if 'web' not in arr.keys():
#                 bot.reply_to(message, f'[-] Error credentials: not valid json', reply_markup=get_markup_cmd())
#                 return
#         except Exception as err:
#             log.error(f'[-] Error: {err}')
#             bot.reply_to(message, f'[-] Error json: {err}', reply_markup=get_markup_cmd())
#             return
#
#         bot.reply_to(message, f'{type(file.content)}', reply_markup=get_markup_cmd())
#         bot.reply_to(message, f'Download torrent: "{message.document.file_name}"', reply_markup=get_markup_cmd())
#         # send_show_torrent(message)
#     else:
#         bot.reply_to(message, f'not implemented type: "{message.document.mime_type}"',
#                      reply_markup=get_markup_cmd())
#     return  # solo esta puesto para que no falle la inspeccion de codigo


@bot.message_handler(func=lambda message: message.chat.id in owner_bot)
def text_not_valid(message: types.Message) -> NoReturn:
    texto: Text = 'unknown command, enter a valid command :)'
    bot.reply_to(message, texto, reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
    return


@bot.message_handler(regexp=".*")
def handler_others(message: types.Message) -> NoReturn:
    log.info(message)
    text: Text = "You're not allowed to perform this action, that's because you're not me.\n" \
                 f'As far as you know, it disappears -.- {str(message)}'
    bot.reply_to(message, text)
    return


def daemon_gcalendar() -> NoReturn:
    """
    Demonio que va comprobando si tiene que ejecutarse un recordatorio
    :return:
    """
    try:
        calendar: GCalendar = GCalendar()
    except Exception as err:
        log.error(f'[-] Error daemon_gcalendar: {err}')
        bot.send_message(owner_bot[1], f'[-] Error daemon_gcalendar: {err}',
                         message_thread_id=topic_bot)
        time.sleep(5)
        os.kill(os.getpid(), signal.SIGUSR1)  # deberia de matar el proceso padre del thread
        log.warning('llego??')
        sys.exit(1)  # creo que no tiene efecto, pero es para el validador semantico

    delay: int = int(config_basic.get('DELAY'))
    num_events: int = int(config_basic.get('NUM_EVENTS'))

    while True:
        # Al capturar el error en el bucle infinito, si falla una vez por x motivo no afectaria,
        # ya que seguiria ejecutandose en siguientes iteraciones
        try:
            log.debug('get calendar and update cron')
            get_events(GCalendar(), calendar_id, file_cron, num_events, bot=None, id_admin=None)
        except Exception as e:
            log.error(f'Fail thread: {e}')
            bot.send_message(owner_bot[1], f'[-] Error thread: {e}', message_thread_id=topic_bot)

        # iteration += 1

        # https://stackoverflow.com/questions/17075788/python-is-time-sleepn-cpu-intensive
        time.sleep(delay)


def daemon_crond() -> NoReturn:
    while True:
        try:
            log.debug('check crond')
            if 'crond' not in list(map(lambda i: i.name(), psutil.process_iter())):
                bot.send_message(owner_bot[1], f'Starting crond',
                                 reply_markup=get_markup_cmd(), message_thread_id=topic_bot)
                os.system('crond')
        except Exception as e:
            log.error(f'Fail thread: {e}')
            bot.send_message(owner_bot[1], f'[-] Error thread: {e}', message_thread_id=topic_bot)

        # https://stackoverflow.com/questions/17075788/python-is-time-sleepn-cpu-intensive
        time.sleep(240)


def main():
    d1 = threading.Thread(target=daemon_gcalendar, name='irrigation_controler_daemon', daemon=True)
    d1.start()

    d2 = threading.Thread(target=daemon_crond, name='cron_daemon', daemon=True)
    d2.start()

    try:
        bot.send_message(owner_bot[1], "Starting bot", reply_markup=get_markup_cmd(),
                         disable_notification=True, message_thread_id=topic_bot)
        log.info('[+] Starting bot')
    except (apihelper.ApiException, exceptions.ReadTimeout) as e:
        log.critical(f'[-] Error in init bot: {e}')
        sys.exit(1)

    # Con esto, le decimos al bot que siga funcionando incluso si encuentra algun fallo.
    # bot.infinity_polling(none_stop=True)
    # Si hay un fallo me interesa que el script termine, para que pueda relanzarse el servicio desde el cron
    bot.infinity_polling(none_stop=False)


if __name__ == "__main__":
    main()
