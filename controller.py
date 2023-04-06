#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from dataclasses import dataclass, field
from typing import Dict, Text, NoReturn, Tuple, List, Any
import sys
# import configparser
# from pathlib import Path
from procamora_utils.logger import get_logging, logging

from ha import get_irrigation_ha, set_irrigation_ha, get_all_irrigation_ha

if sys.platform == 'darwin':
    log: logging = get_logging(verbose=True, name='gpio')
else:  # raspberry
    log: logging = get_logging(verbose=False, name='gpio')


# pinout  # bash
# sudo raspi-gpio get
# gpio readall  # bash  # gpio: command not found


@dataclass
class Controller:
    back_left: Dict = field(default_factory=dict)
    back_right: Dict = field(default_factory=dict)
    front: Dict = field(default_factory=dict)
    vegetable: Dict = field(default_factory=dict)

    def __post_init__(self):
        self.all_switchs: List[Dict[Text, Any]] = get_all_irrigation_ha(prefix_entity="switch.irrigation")

        for i in self.all_switchs:
            if re.search(r'Back Garden Left', i['friendly_name'], re.IGNORECASE):
                self.back_left.update({'id': i['entity_id'], 'name': i['friendly_name']})
            elif re.search(r'Back Garden Right', i['friendly_name'], re.IGNORECASE):
                self.back_right.update({'id': i['entity_id'], 'name': i['friendly_name']})
            elif re.search(r'Front Garden', i['friendly_name'], re.IGNORECASE):
                self.front.update({'id': i['entity_id'], 'name': i['friendly_name']})
            elif re.search(r'Vegetable', i['friendly_name'], re.IGNORECASE):
                self.vegetable.update({'id': i['entity_id'], 'name': i['friendly_name']})

        if 'id' not in self.back_left or 'id' not in self.back_right or 'id' not in self.front or 'id' not in self.vegetable:
            log.critical('[-] Failed get variables HA')
            log.error(self)
            sys.exit(134)

    def get_status(self) -> Dict[Text, bool]:
        response: Dict = {}
        all_switchs: List[Dict[Text, Any]] = get_all_irrigation_ha(prefix_entity="switch.irrigation")
        _ = list(map(lambda e: response.update({e['friendly_name']: e['state']}), all_switchs))

        return response

    def is_any_active(self) -> Tuple[bool, Dict]:
        status: Dict = self.get_status()
        return 'on' in status.values(), status

    def get_entity_id(self, friendly_name: Text) -> Text:
        # all_switchs: List[Dict[Text, Any]] = get_all_irrigation_ha(prefix_entity="switch.irrigation")
        response: List = list(
            filter(lambda e: re.search(friendly_name, e['friendly_name'], re.IGNORECASE), self.all_switchs))
        # log.critical(response)
        return response[0]['entity_id']

    def get_friendly_name(self, entity_id: Text) -> Text:
        # all_switchs: List[Dict[Text, Any]] = get_all_irrigation_ha(prefix_entity="switch.irrigation")
        response: List = list(filter(lambda e: e['entity_id'] == entity_id, self.all_switchs))
        # log.critical(response)
        return response[0]['friendly_name']

    def set_state(self, entity_id: Text = '', state: Text = 'off', friendly_name: Text = '') -> NoReturn:
        if not re.search(r'^(on|off)$', str(state)):
            log.error(f'[-] not valid state: {state} for {entity_id}({friendly_name})')
            return

        if entity_id == '':
            entity_id: Text = self.get_entity_id(friendly_name)
            log.debug(f'zone: {entity_id}, name: {friendly_name}, state:{state}')

        response = set_irrigation_ha(state=state, entity_id=entity_id)
        log.debug(response)

    def stop_all(self) -> NoReturn:
        if self.is_any_active():
            # all_switchs: List[Dict[Text, Any]] = get_all_irrigation_ha(prefix_entity="switch.irrigation")
            response_filter: List = list(filter(lambda e: e['state'] == 'on', self.all_switchs))
            _ = list(map(lambda e: self.set_state(e['entity_id'], 'off'), response_filter))
        else:
            log.debug('all zones off')

    @staticmethod
    def is_active(entity_id: Text) -> bool:
        return get_irrigation_ha(entity_id).json()['state'].lower() == 'on'


def main():
    controller: Controller = Controller()
    log.debug(controller.get_status())
    # controller.stop_all()
    # controller.set_state(controller.back_right['id'], 'on')
    # controller.set_state(friendly_name=controller.back_left['name'], state='on')
    # log.debug(controller.get_status())
    # controller.stop_all()
    # log.debug(controller.get_status())


if __name__ == '__main__':
    main()
