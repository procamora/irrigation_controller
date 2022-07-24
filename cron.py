#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
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
            self.commands.append(f'{cron}   {self.user}  {cmd}')

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

    def write(self, file: Path) -> bool:
        new_cron: Text = self.to_cron()
        if file.exists():  # si existe veo si hay diferencias para actualizarlo
            if new_cron != file.read_text():
                log.info('write cron')
                file.write_text(new_cron)
                return True
            else:
                log.debug('same files cron')
                return False
        else:
            log.info('write cron')
            file.write_text(new_cron)
            return True

    @staticmethod
    def format_text(param_text: bytes) -> Text:
        """
        Metodo para formatear codigo, es usado para formatear las salidas de las llamadas al sistema
        :param param_text:
        :return:
        """
        if param_text is not None:
            text = param_text.decode('utf-8')
            return str(text)
        return ''  # Si es None retorno string vacio

    @staticmethod
    def restart_systemd():
        command: Text = 'sudo systemctl restart cron'
        execute = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = execute.communicate()
        log.debug(f'{Cron.format_text(stdout)}')
        log.debug(f'{Cron.format_text(stderr)}')
