#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Text, Optional

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from procamora_utils.logger import get_logging, logging

from cron import Cron

log: logging = get_logging(True, 'calendar')


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
        log.warn(f'{token_path} => exit:{token_path.exists()}')

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
                log.info(f"{calendar_list_entry['summary']} => {calendar_list_entry['id']}")
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

    def get_irrigation(self, calendar_id: Text, num_events: 30) -> Optional[Cron]:
        log.info(self.service)
        # Call the Calendar API
        now: Text = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        log.info(f'Getting the upcoming {num_events} events')
        events_result: Dict = self.service.events().list(calendarId=calendar_id,
                                                         timeMin=now,
                                                         maxResults=num_events,
                                                         singleEvents=True,
                                                         orderBy='startTime').execute()
        if not events_result['items']:
            log.warning('No upcoming events found.')
            return None

        cron = Cron(user='procamora')
        cron.command(f'# Verify service active')
        cron.command(
            f'systemctl -q is-active mio_bot_irrigation.service && echo YES || sudo /usr/bin/systemctl restart mio_bot_irrigation.service',
            '*/10', '*', '*', '*', '*')
        cron.command(f'# Backup closed if open relay at sun day')
        cron.command(f'python3 ~/irrigation_controller/controller_cli.py -z Vegetable -na -nn', 0, 9, '*', '*', '*')
        cron.command(f'python3 ~/irrigation_controller/controller_cli.py -z Back -na -nn', 0, 9, '*', '*', '*')
        cron.command(f'python3 ~/irrigation_controller/controller_cli.py -z Front -na -nn', 0, 9, '*', '*', '*')
        #  /home/pi/tg/bin/telegram-cli -e 'msg domotica_pablo "/modo_automatico on 23"' >/tmp/tg_on.log 2>/tmp/tg_on_err.log
        cron.command(f'# Zones')

        # Prints the start and name of the next 10 events
        for event in events_result['items']:
            start = event['start'].get('dateTime')
            end = event['end'].get('dateTime')
            if start is None or end is None:  # skip event all day
                log.warning(f'skip {event["summary"]}')
                continue

            # log.info(f'{start} {end} {event["summary"]}')
            dt_start: datetime = datetime.fromisoformat(event['start'].get('dateTime'))
            dt_end: datetime = datetime.fromisoformat(event['end'].get('dateTime'))

            cron.command(f'python3 ~/irrigation_controller/controller_cli.py -z {event["summary"]} -a',
                         dt_start.minute, dt_start.hour, dt_start.day, dt_start.month, '*')
            cron.command(f'python3 ~/irrigation_controller/controller_cli.py -z {event["summary"]} -na',
                         dt_end.minute, dt_end.hour, dt_end.day, dt_end.month, '*')

        return cron


def main():
    calendar = GCalendar()
    # calendar.get_calendar_list()
    calendar.get_irrigation('<CALENDAR_ID>', 10)


if __name__ == '__main__':
    main()
