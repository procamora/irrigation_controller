#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import print_function

import os.path
import sys
from datetime import datetime
from typing import Dict, List, Set

from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
# from plan import Plan
from procamora_utils.logger import get_logging, logging

from cron import Cron

log: logging = get_logging(True, 'calendar')


def auth():
    # If modifying these scopes, delete the file token.json.
    scopes = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/calendar.events.readonly'
    ]

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


class GCalendar:

    def __init__(self):
        try:
            creds = auth()
            print(type(creds))
            self.service = build('calendar', 'v3', credentials=creds)
        except GoogleAuthError as err:
            log.critical(err)
            sys.exit(0)

    def get_calendar_list(self):
        page_token = None
        while True:
            calendar_list: Dict = self.service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                log.info(f"{calendar_list_entry['summary']} => {calendar_list_entry['id']}")
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

    def other(self):
        log.info(self.service)
        # Call the Calendar API
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        log.info('Getting the upcoming 10 events')
        events_result: Dict = self.service.events().list(calendarId='q9sg6klvberttgejc7k31qar6g@group.calendar.google.com',
                                                         timeMin=now,
                                                         maxResults=10,
                                                         singleEvents=True,
                                                         orderBy='startTime').execute()
        if not events_result['items']:
            log.warning('No upcoming events found.')
            return

        cron = Cron(user='procamora')
        cron.command(f'# Backup closed if open relay')
        cron.command(f'set_off ZONA1', 0, 9, '*', '*', '*')
        cron.command(f'set_off ZONA2', 0, 9, '*', '*', '*')
        cron.command(f'set_off ZONA3', 0, 9, '*', '*', '*')
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

            cron.command(f'set_on {event["summary"]}', dt_start.minute, dt_start.hour, dt_start.day, dt_start.month, '*')
            cron.command(f'set_off {event["summary"]}', dt_end.minute, dt_end.hour, dt_end.day, dt_end.month, '*')

        log.info(cron.to_cron())
        # log.info(cron.cron_content)
        # cron.run('check')
        # cron.run('write')

    # @staticmethod
    # def get_event_recurence(events: List[Dict]):
    #     asd: Set = set(map(lambda i: i["summary"], events))
    #     log.info(asd)


def main():
    calendar = GCalendar()
    # calendar.get_calendar_list()
    calendar.other()


if __name__ == '__main__':
    main()
