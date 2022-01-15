# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

import argparse
import configparser

from secbootctl.core import App, AppError, CliCmdManager, Config, ControllerFactory, Dispatcher, Router
from secbootctl.helpers.cli import CliPrintHelper


def main() -> int:
    exit_code: int = 0

    try:
        config: Config = Config(configparser.ConfigParser())

        App(
            config,
            CliCmdManager(argparse.ArgumentParser(add_help=False)),
            Router(),
            Dispatcher(ControllerFactory(config))
        ).run()
    except AppError as app_error:
        cli_print_helper: CliPrintHelper = CliPrintHelper()
        cli_print_helper.print_error(app_error.message, app_error.code)
        exit_code = app_error.code

    return exit_code
