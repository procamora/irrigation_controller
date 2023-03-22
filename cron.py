#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Text, List, NoReturn, Any, Tuple
import sys
import re
from datetime import datetime

import jinja2
from procamora_utils.logger import get_logging, logging

if sys.platform == 'darwin':
    log: logging = get_logging(verbose=True, name='cron')
else:  # raspberry
    log: logging = get_logging(verbose=False, name='cron')


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
            # log.debug(cron)
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
        # log.debug(cmd)
        render: Text = template_row.render(commands=self.commands, user=self.user)
        return render

    def write(self, file: Path) -> Tuple[bool, Text, Text]:
        new_cron: Text = self.to_cron()
        if file.exists():  # si existe veo si hay diferencias para actualizarlo
            actual_cron: Text = file.read_text()
            if new_cron.rstrip() != actual_cron.rstrip():
                log.info(f'update cron, original_size:{len(actual_cron)}, new_size:{len(new_cron)}')
                # file.write_text(new_cron)  # no quiero ejecutar como root el script, tee esta en sudoers sin password
                stdout, stderr = self.sudo_tee_cron(new_cron, file)
                return True, stdout, stderr
            else:
                log.debug('same files cron')
                return False, '', ''
        else:
            log.info('create cron')
            # file.write_text(new_cron)  # no quiero ejecutar como root el script, tee esta en sudoers sin password
            stdout, stderr = self.sudo_tee_cron(new_cron, file)
            return True, stdout, stderr

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
    def sudo_tee_cron(content: Text, path: Path) -> Tuple[Text, Text]:
        command: Text = f'echo \'{content}\' | sudo /usr/bin/tee {str(path)} >/dev/null'
        execute = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = execute.communicate()
        log.debug(f'stdout: {Cron.format_text(stdout)}')
        log.debug(f'stderr: {Cron.format_text(stderr)}')
        return Cron.format_text(stdout), Cron.format_text(stderr)

    @staticmethod
    def cron_to_list(file: Path) -> List[List[Text]]:
        lines: List[List[Text]] = []
        for line in file.read_text().split('\n'):
            # -a final para solo ver las activacaiones
            match: re.Match = re.search(
                r'^(?P<minute>\d+)( )+(?P<hour>\d+)( )+(?P<day>\d+)( )+(?P<month>\d+).*(controller_cli\.py)( )+(-\w+)( )+(?P<zone>.*)( )+-a$',
                line)
            if match:
                c = match.groupdict()
                dt: datetime = datetime.strptime(f'{c["month"]}/{c["day"]} {c["hour"]}:{c["minute"]}', "%m/%d %H:%M")
                lines.append([f'{c["zone"]}', dt.strftime('%b %d at %H:%M')])

        log.debug(lines)
        return lines

    # @staticmethod
    # def sudo_restart_cron():
    #     command: Text = 'sudo /usr/bin/systemctl restart cron.service'
    #     execute = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     stdout, stderr = execute.communicate()
    #     log.debug(f'stdout: {Cron.format_text(stdout)}')
    #     log.debug(f'stderr: {Cron.format_text(stderr)}')


def main():
    cron = Cron(user='test')
    cron.cron_to_list(Path('./cron.debug'))
    log.info(cron.to_cron())


if __name__ == "__main__":
    main()
