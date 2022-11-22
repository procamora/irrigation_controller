#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from requests import get, post
import configparser
from pathlib import Path
from typing import Text


def get_irrigation_ha(entity: Text = "input_boolean.irrigation") -> requests.Response:
    config: configparser.ConfigParser = configparser.ConfigParser()
    config.read(Path(Path(__file__).resolve().parent, "settings.cfg"))
    basics: configparser.SectionProxy = config["BASICS"]

    url = f"{basics['HOST_HA']}/api/states/{entity}"
    headers = {
        "Authorization": f"Bearer {basics['TOKEN_HA']}",
        "content-type": "application/json",
    }
    response: requests.Response = get(url, headers=headers)
    return response


def set_irrigation_ha(state: Text, entity: Text = "input_boolean.irrigation"):
    config: configparser.ConfigParser = configparser.ConfigParser()
    config.read(Path(Path(__file__).resolve().parent, "settings.cfg"))
    basics: configparser.SectionProxy = config["BASICS"]

    url = f"{basics['HOST_HA']}/api/states/{entity}"
    headers = {
        "Authorization": f"Bearer {basics['TOKEN_HA']}",
        "content-type": "application/json",
    }

    response: requests.Response = post(url, headers=headers, json={"state": state})
    return response


def main():
    print(get_irrigation_ha().text)
    set_irrigation_ha('on')
    print(get_irrigation_ha().text)
    set_irrigation_ha('off')
    print(get_irrigation_ha().text)


if __name__ == '__main__':
    main()
