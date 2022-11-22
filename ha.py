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

    url = f"{config['HOST_HA']}/api/states/{entity}"
    headers = {
        "Authorization": f"Bearer {config['TOKEN_HA']}",
        "content-type": "application/json",
    }
    response: requests.Response = get(url, headers=headers)
    return response


def set_irrigation_ha(state: Text, entity: Text = "input_boolean.irrigation"):
    config: configparser.ConfigParser = configparser.ConfigParser()
    config.read(Path(Path(__file__).resolve().parent, "settings.cfg"))

    url = f"{config['HOST_HA']}/api/states/{entity}"
    headers = {
        "Authorization": f"Bearer {config['TOKEN_HA']}",
        "content-type": "application/json",
    }

    response: requests.Response = post(url, headers=headers, json={"state": state})
    return response
