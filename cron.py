#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from pathlib import Path
from typing import Text, List, NoReturn, Any

import jinja2
from procamora_utils.logger import get_logging, logging

log: logging = get_logging(True, 'cron')


@dataclass
class Cron:
    user: Text
    commands: List[Text] = field(default_factory=list)

    # def __post_init__(self):
    #     self.commands.append()

    def command(self, cmd: Text, minute: Any = '*', hour: Any = '*', day: Any = '*',
                month: Any = '*', week: Any = '*') -> NoReturn:
        if cmd[0] == '#':
            self.commands.append(f'{cmd}')
        else:
            if len(str(hour)) == 1:
                hour = f'{hour} '
            if len(str(day)) == 1:
                day = f'{day} '
            if len(str(minute)) == 1:
                minute = f'{minute} '
            if len(str(month)) == 1:
                month = f'{month} '

            cron = f'{minute} {hour} {day} {month} {week}'
            # log.info(cron)
            self.commands.append(f'{cron}    {cmd}')

    def to_cron(self) -> Text:
        working_path: Path = Path(__file__).resolve().parent
        template_path: Path = Path('cron.j2')

        jinja_env: jinja2.Environment = jinja2.Environment(
            line_statement_prefix='%%', line_comment_prefix='%#', trim_blocks=True, autoescape=False,
            loader=jinja2.FileSystemLoader(str(working_path))
        )
        template_row: jinja2.environment.Template = jinja_env.get_template(str(template_path))
        # cmd = '\n'.join(map(lambda i: f'{i}', self.commands))
        # log.info(cmd)
        render: Text = template_row.render(commands=self.commands, user=self.user)
        return render

    # @staticmethod
    # def generate_cmd(cron: Text, cmd: Text) -> Text:
    #     return
