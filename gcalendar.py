#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import configparser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Text, Optional
import sys

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from procamora_utils.logger import get_logging, logging

from cron import Cron

if sys.platform == 'darwin':
    log: logging = get_logging(verbose=True, name='gcalendar')
else:  # raspberry
    log: logging = get_logging(verbose=False, name='gcalendar')


# https://developers.google.com/calendar/api/quickstart/python
def auth() -> Credentials:
    # If modifying these scopes, delete the file token.json.
    scopes: List[Text] = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events.readonly'
    ]

    creds: Optional[Credentials] = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    credentials_path: Path = Path(Path(__file__).resolve().parent, 'credentials.json')
    token_path: Path = Path(Path(__file__).resolve().parent, 'token.json')
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)
    else:
        log.warning(f'{token_path} => exit:{token_path.exists()}')

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), scopes)
            creds = flow.run_local_server(port=0, open_browser=False)
        # Save the credentials for the next run
        token_path.write_text(creds.to_json())
    return creds


class GCalendar:
    def __init__(self):
        try:
            creds: Credentials = auth()
            self.service = build('calendar', 'v3', credentials=creds)
        except GoogleAuthError as err:
            log.critical(err)
            raise Exception(err)

    def get_calendar_list(self):
        page_token = None
        while True:
            calendar_list: Dict = self.service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                log.debug(f"{calendar_list_entry['summary']} => {calendar_list_entry['id']}")
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

    def get_irrigation(self, calendar_id: Text, num_events: 30) -> Optional[Cron]:
        # Call the Calendar API
        now: Text = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        log.debug(f'Getting the upcoming {num_events} events')
        events_result: Dict = self.service.events().list(calendarId=calendar_id,
                                                         timeMin=now,
                                                         maxResults=num_events,
                                                         singleEvents=True,
                                                         orderBy='startTime').execute()

        if not events_result['items']:
            log.warning('No upcoming events found.')
            return None

        log.debug(f'Getting the upcoming {num_events} events > {len(events_result["items"])}')
        cron = Cron(user='procamora')
        # cron.command(f'# Verify service active')
        # cron.command(
        #     f'systemctl -q is-active mio_bot_irrigation.service && echo YES || '
        #     f'sudo /usr/bin/systemctl restart mio_bot_irrigation.service',
        #     '*/10', '*', '*', '*', '*')
        cron.command(f'# Watchdog')
        cron.command(f'python3 ~/watchdog.py', '*/10', '*', '*', '*', '*')
        cron.command(f'# Watchdog')
        cron.command(f'python3 ~/cron_refresh.py', '*/30', '*', '*', '*', '*')
        cron.command(f'# Backup closed if open relay at sun day')
        cron.command(f'python3 ~/controller_cli.py -e switch.irrigation_back_garden_left -s off -nn', 0, 9, '*', '*', '*')
        cron.command(f'python3 ~/controller_cli.py -e switch.irrigation_back_garden_right -s off -nn', 0, 9, '*', '*', '*')
        cron.command(f'python3 ~/controller_cli.py -e switch.irrigation_front_garden -s off -nn', 0, 9, '*', '*', '*')
        cron.command(f'python3 ~/controller_cli.py -e switch.irrigation_vegetable -s off -nn', 0, 9, '*', '*', '*')
        #  /home/pi/tg/bin/telegram-cli -e 'msg domotica_pablo "/modo_automatico on 23"' >/tmp/tg_on.log 2>/tmp/tg_on_err.log
        cron.command(f'# Zones')

        # Prints the start and name of the next 10 events
        for event in events_result['items']:
            start = event['start'].get('dateTime')
            end = event['end'].get('dateTime')
            if start is None or end is None:  # skip event all day
                log.warning(f'skip {event["summary"]}')
                continue

            # log.debug(f'{start} {end} {event["summary"]}')
            dt_start: datetime = datetime.fromisoformat(event['start'].get('dateTime'))
            dt_end: datetime = datetime.fromisoformat(event['end'].get('dateTime'))

            cron.command(f'python3 ~/controller_cli.py -f "{event["summary"]}" -s on',
                         dt_start.minute, dt_start.hour, dt_start.day, dt_start.month, '*')
            cron.command(f'python3 ~/controller_cli.py -f "{event["summary"]}" -s off',
                         dt_end.minute, dt_end.hour, dt_end.day, dt_end.month, '*')

        return cron


def main():
    config: configparser.ConfigParser = configparser.ConfigParser()
    file_config: Path = Path(Path(__file__).resolve().parent, "settings.cfg")
    config.read(file_config)
    calendar = GCalendar()
    calendar.get_calendar_list()
    events: Cron = calendar.get_irrigation(config["BASICS"]["CALENDAR_ID"], 10)
    log.info(events.to_cron())


if __name__ == '__main__':
    main()
