# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

import glob
import textwrap
from pathlib import Path

from secbootctl.core import AppController, BaseSubcmdCreator


class FileController(AppController):
    def list(self, all: bool) -> None:
        """Lists EFI or optionally all files on EFI System Partition (ESP) with their signing status."""
        file_extension: str = '.efi' if not all else ''
        file_paths: list = glob.glob(str(self._config.esp_path / '**' / ('*' + file_extension)), recursive=True)

        # If glob works case sensitive or insensitive seems to depend on the underlying filesystem. Thus next to
        # search for ".efi" we search for ".EFI" too and merge both results.
        if not all:
            file_paths2: list = glob.glob(
                str(self._config.esp_path / '**' / ('*' + file_extension.upper())), recursive=True
            )
            file_paths = list({*file_paths, *file_paths2})

        file_paths.sort()

        for file_path in file_paths:
            file_path: Path = Path(file_path)

            if file_path.is_dir():
                continue

            signed_message: str = '\u2717 not signed'

            if self._sb_helper.verify_file(file_path):
                signed_message = '\u2714 signed'

            print(f'{file_path}\n{"Status":>10} {signed_message}')

    def sign(self, file_path: str) -> None:
        self._sign_file(Path(file_path))

    def verify(self, file_path: str) -> None:
        self._verify_file(Path(file_path))


class FileSubcmdCreator(BaseSubcmdCreator):
    def create(self, cli_subparsers):
        fl_cli_subparser = self._add(cli_subparsers, 'file:list', 'list files on ESP with signing status',
                                     textwrap.dedent('''
            Lists all EFI files (files with ".efi" file extension) found on the
            EFI System Partition (ESP) and their signing status. Optionally to list all
            files instead of only the EFI files use the "--all" option.
        '''))
        fl_cli_subparser.add_argument('--all', action='store_true', help='list all files on the ESP')
        fs_cli_subparser = self._add(cli_subparsers, 'file:sign', 'sign given file', textwrap.dedent('''
            Sign the given file.
        '''))
        fs_cli_subparser.add_argument('file_path', help='file to be signed')
        fv_cli_subparser = self._add(cli_subparsers, 'file:verify', 'verify signature of given file',
                                     textwrap.dedent('''
            Verify signature of the given file.
        '''))
        fv_cli_subparser.add_argument('file_path', help='file to be verified')
