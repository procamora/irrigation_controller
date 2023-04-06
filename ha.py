#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from requests import get, post
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
import logging
import configparser
from pathlib import Path
import re
from typing import Text, Dict, Any, List
from procamora_utils import get_logging
import sys

disable_warnings(InsecureRequestWarning)

if sys.platform == 'darwin':
    log: logging = get_logging(verbose=True, name='ha')
else:  # raspberry
    log: logging = get_logging(verbose=False, name='ha')

FILE_CONFIG: Path = Path(Path(__file__).resolve().parent, "settings.cfg")
if not FILE_CONFIG.exists():
    log.critical(f'File {FILE_CONFIG} not exists and is necesary')
    sys.exit(1)

config: configparser.ConfigParser = configparser.ConfigParser()
config.read(FILE_CONFIG)

basics: configparser.SectionProxy = config["BASICS"]


# ha_switchs: configparser.SectionProxy = config["HA_SWITCHS"]


def get_all_irrigation_ha(prefix_entity: Text = "switch.irrigation") -> List[Dict[Text, Any]]:
    response_list: List = []
    url = f"{basics['HOST_HA']}/api/states"
    headers = {
        "Authorization": f"Bearer {basics['TOKEN_HA']}",
        "content-type": "application/json",
    }
    response: requests.Response = get(url, headers=headers, verify=False)
    if response.status_code != 200:
        log.debug(response)

    response_filter: List = list(filter(lambda e: re.search(rf'^{prefix_entity}', e['entity_id']), response.json()))
    # log.debug(response_filter)
    _ = list(map(lambda e: response_list.append(
        {'entity_id': e['entity_id'],
         'state': e['state'],
         'friendly_name': e['attributes']['friendly_name'] if 'friendly_name' in e['attributes'] else '----'
         }), response_filter))

    return response_list


def get_irrigation_ha(entity_id: Text) -> requests.Response:
    url = f"{basics['HOST_HA']}/api/states/{entity_id}"
    headers = {
        "Authorization": f"Bearer {basics['TOKEN_HA']}",
        "content-type": "application/json",
    }
    response: requests.Response = get(url, headers=headers, verify=False)
    if response.status_code != 200:
        log.debug(response)
    return response


def set_irrigation_ha(state: Text, entity_id):
    url = f"{basics['HOST_HA']}/api/services/switch/turn_{state}"
    headers = {
        "Authorization": f"Bearer {basics['TOKEN_HA']}",
        "content-type": "application/json",
    }

    response: requests.Response = post(url, headers=headers, json={"entity_id": entity_id}, verify=False)
    if response.status_code != 200:
        log.info(url)
        log.info({"entity_id": entity_id})
        log.debug(response)
        log.info(response.text)
    return response


def main():
    log.info(get_all_irrigation_ha())
    # log.info(ha_switchs['BACK_LEFT'])
    # log.info(get_irrigation_ha(ha_switchs['BACK_LEFT']).text)
    # # set_irrigation_ha('on', ha_switchs['BACK_LEFT'])
    # # log.info(get_irrigation_ha(ha_switchs['BACK_LEFT']).text)
    # set_irrigation_ha('off', ha_switchs['BACK_LEFT'])
    # log.info(get_irrigation_ha(ha_switchs['BACK_LEFT']).text)
    # log.info(get_irrigation_ha(ha_switchs['BACK_LEFT']).json()['state'])


if __name__ == '__main__':
    main()
