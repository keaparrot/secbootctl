# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

import textwrap

from secbootctl.core import AppController, BaseSubcmdCreator
from secbootctl.env import Env


class ConfigController(AppController):
    def list(self) -> None:
        """Lists configuration values configured in configuration file."""
        print(f'{"Config-Name":35} Config-Value\n{"---":35} ---')

        for config_key, config_value in self._config.config_data.items():
            print(f'{config_key:35} {config_value}')

        print(f'\nConfiguration file: "{Env.APP_CONFIG_FILE_PATH}"')


class ConfigSubcmdCreator(BaseSubcmdCreator):
    def create(self, cli_subparsers):
        self._add(cli_subparsers, 'config:list', 'list current config', textwrap.dedent(f'''
            List the current configuration. For {Env.APP_NAME} to work properly on your
            system you might need to adjust the default configuration. The config
            file is expected to be in "{Env.APP_CONFIG_FILE_PATH}".
        '''))
