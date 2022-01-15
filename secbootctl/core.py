# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

import argparse
import configparser
import importlib
import textwrap
from pathlib import Path
from pkgutil import iter_modules
from types import ModuleType
from typing import Any
from typing import Optional

import secbootctl.features
from secbootctl.env import Env
from secbootctl.helpers.cli import CliPrintHelper, CliCmdUsageHelpFormatter
from secbootctl.helpers.kernelos import KernelOsHelper
from secbootctl.helpers.secureboot import SecureBootHelper


class App:
    def __init__(self, config: Config, cli_cmd_manager: CliCmdManager, router: Router, dispatcher: Dispatcher):
        self._config: Config = config
        self._cli_cmd_manager: CliCmdManager = cli_cmd_manager
        self._router: Router = router
        self._dispatcher: Dispatcher = dispatcher

    def run(self) -> None:
        Env.load()
        self._config.load(Env.APP_CONFIG_FILE_PATH)
        self._cli_cmd_manager.init_commands(self._config.esp_path)
        self._dispatcher.dispatch(
            self._router.match(
                self._cli_cmd_manager.parse_request()
            )
        )


class AppError(Exception):
    """Error class used for all explicit raised errors."""

    def __init__(self, message: str, code: Optional[int] = 1):
        self._message: str = message
        self._code: int = code

    @property
    def message(self) -> str:
        return self._message

    @property
    def code(self) -> int:
        return self._code


class Config:
    def __init__(self, config_parser: configparser.ConfigParser):
        self._config_parser: configparser.ConfigParser = config_parser
        self._config_data: dict = {}

    def load(self, config_file_path: Path) -> None:
        readable_files: list = self._config_parser.read(config_file_path)

        if not readable_files:
            raise AppError(f'could not read configuration file "{config_file_path}"')

        for config_key, config_value in self._config_parser['DEFAULT'].items():
            self._config_data[config_key] = config_value

    @property
    def config_data(self) -> dict:
        return self._config_data

    @property
    def boot_path(self) -> Path:
        return Path(self._get('boot_path'))

    @property
    def esp_path(self) -> Path:
        return Path(self._get('esp_path'))

    @property
    def sb_keys_path(self) -> Path:
        return Path(self._get('sb_keys_path'))

    @property
    def default_kernel_name(self) -> str:
        return self._get('default_kernel')

    @property
    def include_microcode(self) -> bool:
        return True if self._get('include_microcode') == 'yes' else False

    @property
    def kernel_image_name_prefix(self) -> str:
        return self._get('kernel_image_name_prefix')

    @property
    def initramfs_image_name_template(self) -> str:
        return self._get('initramfs_image_name_template')

    @property
    def microcode_image_name(self) -> str:
        return self._get('microcode_image_name')

    @property
    def bootloader_menu_editor(self) -> str:
        return self._get('bootloader_menu_editor')

    @property
    def bootloader_menu_timeout(self) -> int:
        return self._get('bootloader_menu_timeout', 5)

    @property
    def package_manager_name(self) -> str:
        return self._get('package_manager')

    def _get(self, key: str, fallback_value: Any = None) -> Any:
        return self._config_data.get(key, fallback_value)


class Router:
    """Resolves cli request data and the result is used by the dispatcher for dispatching the cli request."""
    def match(self, cli_request_data: dict) -> dict:
        command_name_split: list = cli_request_data['command_name'].split(':', 1)
        module_name: str = command_name_split[0] if len(command_name_split) == 2 else 'misc'
        controller_name = module_name.capitalize() + 'Controller'
        module_name = 'secbootctl.features.' + module_name
        action_name: str = command_name_split[1] if len(command_name_split) == 2 else command_name_split[0]
        action_name = action_name.replace('-', '_')
        cli_request_data.pop('command_name')

        return {
            'module_name': module_name,
            'controller_name': controller_name,
            'action_name': action_name,
            'params': cli_request_data
        }


class Dispatcher:
    """Dispatches cli request by invoking the appropriate controller action."""
    def __init__(self, controller_factory: ControllerFactory):
        self._controller_factory: ControllerFactory = controller_factory

    def dispatch(self, route_data: dict) -> None:
        controller: AppController = self._controller_factory.create(
            route_data['module_name'], route_data['controller_name'], self
        )
        getattr(controller, route_data['action_name'])(**route_data['params'])


class CliCmdManager:
    def __init__(self, cli_parser: argparse.ArgumentParser):
        self._cli_parser: argparse.ArgumentParser = cli_parser

    def init_commands(self, esp_path: Path) -> None:
        self._cli_parser.formatter_class = CliCmdUsageHelpFormatter
        self._cli_parser._positionals.title = 'Commands'
        self._cli_parser._optionals.title = 'Options'
        self._cli_parser.epilog = textwrap.dedent(f'''
            Use "{Env.APP_NAME} [command] --help" for more information about a command.

            Config:
              For {Env.APP_NAME} to work properly on your system you might need to adjust
              the default config. The config file is expected
              to be in "{Env.APP_CONFIG_FILE_PATH}".

              To list the current config use "{Env.APP_NAME} config:list"

            Package-Manager-Integration:
              Instead of manually calling the appropriate commands after each install,
              update or removal of kernel relevant packages it is possible to automate
              this process by using package manager hooks.

              Currently the following package managers are supported:
              {', '.join(Env.SUPPORTED_PACKAGE_MANAGERS)}
        ''')

        self._cli_parser.add_argument('-h', '--help', action='help', help='show this help')
        self._cli_parser.add_argument('-V', '--version', action='version', version=Env.APP_TITLE, help='show version')

        cli_subparsers = self._cli_parser.add_subparsers(dest='command_name', metavar='[command]')

        # loop through all modules in the feature directory and call BaseSubcmdCreator:create
        for submodule in iter_modules(secbootctl.features.__path__):
            feature_module: ModuleType = importlib.import_module('secbootctl.features.' + submodule.name)
            feature_subcommand_creator: BaseSubcmdCreator = getattr(
                feature_module, submodule.name.capitalize() + 'SubcmdCreator'
            )(esp_path)
            feature_subcommand_creator.create(cli_subparsers)

    def parse_request(self) -> dict:
        cli_args = self._cli_parser.parse_args()

        if cli_args.command_name is None:
            self._cli_parser.parse_args(['--help'])

        return vars(cli_args)


class BaseSubcmdCreator:
    def __init__(self, esp_path: Path):
        self._esp_path: Path = esp_path

    def create(self, cli_subparsers):
        pass

    def _add(self, cli_subparsers, name: str, help_message: str, help_epilog_message: str = ''):
        cli_subparser = cli_subparsers.add_parser(name, help=help_message, add_help=False,
                                                  formatter_class=CliCmdUsageHelpFormatter)
        cli_subparser._positionals.title = 'Arguments'
        cli_subparser._optionals.title = 'Options'
        cli_subparser.epilog = help_epilog_message
        self._add_help_option(cli_subparser)

        return cli_subparser

    def _add_help_option(self, cli_parser) -> None:
        cli_parser.add_argument('-h', '--help', action='help', help='show this help')


class ControllerFactory:
    def __init__(self, config: Config):
        self._config: Config = config

    def create(self, module_name: str, controller_name: str, dispatcher: Dispatcher) -> AppController:
        feature_module: ModuleType = importlib.import_module(module_name)

        return getattr(feature_module, controller_name)(self._config, dispatcher)


class AppController:
    """Base controller class."""
    def __init__(self, config: Config, dispatcher: Dispatcher):
        self._config: Config = config
        self._dispatcher: Dispatcher = dispatcher
        self._cli_print_helper: CliPrintHelper = CliPrintHelper()
        self._kernel_os_helper: KernelOsHelper = KernelOsHelper(config)
        self._sb_helper: SecureBootHelper = SecureBootHelper(config.sb_keys_path)

        self._kernel_os_helper.check_requirements()

    def _forward(self, feature_name: str, action_name: str, params: Optional[dict] = None):
        """Invokes controller action for given feature, controller and action name."""
        if params is None:
            params = {}

        self._dispatcher.dispatch({
            'module_name': 'secbootctl.features.' + feature_name,
            'controller_name': feature_name.capitalize() + 'Controller',
            'action_name': action_name,
            'params': params}
        )

    def _print_status(self, message: str, status: CliPrintHelper.Status = CliPrintHelper.Status.PENDING) -> None:
        self._cli_print_helper.print_status(message, status)

    def _sign_file(self, file_path: Path) -> None:
        self._print_status(f'signing: {file_path}')

        if not self._sb_helper.sign_file(file_path):
            raise AppError(f'failed to sign: {file_path}')

        self._print_status(f'signed: {file_path}', CliPrintHelper.Status.SUCCESS)

    def _verify_file(self, file_path: Path) -> None:
        self._print_status(f'verifying signature: {file_path}')

        if self._sb_helper.verify_file(file_path):
            self._print_status(f'valid signature: {file_path}', CliPrintHelper.Status.SUCCESS)
        else:
            self._print_status(f'invalid signature: {file_path}', CliPrintHelper.Status.ERROR)
