# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

import argparse
from enum import Enum
from typing import Optional

from secbootctl.env import Env


class CliPrintHelper:
    class Status(Enum):
        PENDING = 'pending'
        SUCCESS = 'success'
        ERROR = 'error'

    def print_status(self, message: str, status: Optional[Status] = Status.PENDING) -> None:
        status_symbols: dict = {
            CliPrintHelper.Status.PENDING: ' ',
            CliPrintHelper.Status.SUCCESS: '\u2713 done:',
            CliPrintHelper.Status.ERROR: '\u2717 failed:'
        }

        print(f'{status_symbols[status]} {message}')

    def print_error(self, message: str, code: int = 1) -> None:
        print(f'\u2717 ERROR: {message} (Code: {code})\n\nUse "{Env.APP_NAME} --help" for more information.')


class CliCmdUsageHelpFormatter(argparse.HelpFormatter):
    """Custom usage formatter that does some dirty stuff with the internal structure of argparse.

    Unfortunately everything in argarse is considered internal and only helper classnames are considered public API.
    But because I really don't like the default formatting of argparse I did this hacky workaround, although
    I'm not happy with it at all.
    """
    def __init__(self, prog, indent_increment=2, max_help_position=30, width=None):
        super().__init__(prog, indent_increment, max_help_position, width)

    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = f'{Env.APP_TITLE}\n\nUsage: '

        return super().add_usage(usage, actions, groups, prefix)

    def _format_action(self, action):
        result = super()._format_action(action)

        if self._is_subparser(action):
            result = '%*s%s' % (self._current_indent, '', result.lstrip())

        return result

    def _format_action_invocation(self, action):
        return '' if self._is_subparser(action) else super()._format_action_invocation(action)

    def _iter_indented_subactions(self, action):
        if self._is_subparser(action):
            try:
                get_subactions = action._get_subactions
            except AttributeError:
                pass
            else:
                yield from get_subactions()
        else:
            for subaction in super()._iter_indented_subactions(action):
                yield subaction

    def _fill_text(self, text, width, indent):
        return ''.join(indent + line for line in text.splitlines(keepends=True))

    def _is_subparser(self, action: object) -> bool:
        return isinstance(action, argparse._SubParsersAction)
