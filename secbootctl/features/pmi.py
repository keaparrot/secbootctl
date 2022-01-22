# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

import glob
import os
import shutil
import sys
import textwrap
from pathlib import Path
from typing import Optional

from secbootctl.core import AppController, BaseSubcmdCreator, AppError
from secbootctl.env import Env
from secbootctl.helpers.cli import CliPrintHelper


class PmiController(AppController):
    PACMAN_HOOK_PATH: Path = Path('/etc/pacman.d/hooks')

    def install(self):
        """Copies the hook files for the configured package manager into the corresponding hook directories."""
        pm_name: str = self._config.package_manager_name

        self._check_package_manager(pm_name)

        self._print_status(f'installing hook files for package manager: {pm_name}')

        getattr(self, '_' + pm_name + '_install')()

        self._print_status(f'installed hook files for package manager: {pm_name}', CliPrintHelper.Status.SUCCESS)

    def remove(self):
        """Removes the hook files for the configured package manager in the corresponding hook directories."""
        pm_name: str = self._config.package_manager_name

        self._check_package_manager(pm_name)

        self._print_status(f'removing hook files for package manager: {pm_name}')

        getattr(self, '_' + pm_name + '_remove')()

        self._print_status(f'removed hook files for package manager: {pm_name}', CliPrintHelper.Status.SUCCESS)

    def hook_callback(self, mode: str, kernel_name: Optional[str] = None):
        """Callback invoked by package manager hook(s)."""
        pm_name: str = self._config.package_manager_name

        self._check_package_manager(pm_name)

        # @todo there is propably a prettier solution...
        if pm_name == 'pacman':
            getattr(self, '_' + pm_name + '_' + mode + '_callback')()
        else:
            getattr(self, '_' + pm_name + '_' + mode + '_callback')(kernel_name)

    def _check_package_manager(self, pm_name: str) -> None:
        if pm_name not in Env.SUPPORTED_PACKAGE_MANAGERS:
            raise AppError(f'configured package manager "{pm_name}" is not supported')

    def _pacman_install(self):
        pm_name: str = self._config.package_manager_name
        hook_path: Path = Env.APP_HOOK_PATH / pm_name

        for hook_file_path in glob.glob(str(hook_path / '*.*')):
            self._copy_hook_file(Path(hook_file_path), self.PACMAN_HOOK_PATH)

    def _pacman_remove(self):
        pm_name: str = self._config.package_manager_name
        hook_path: Path = Env.APP_HOOK_PATH / pm_name

        for hook_file_path in glob.glob(str(hook_path / '*.*')):
            hook_file_path: Path = Path(hook_file_path)
            target_hook_file_path: Path = self.PACMAN_HOOK_PATH / hook_file_path.name
            target_hook_file_path.unlink(missing_ok=True)

    def _pacman_update_callback(self):
        boot_path: Path = self._config.boot_path
        kernel_image_paths: list = glob.glob(str(boot_path / (self._config.kernel_image_name_prefix + '-*')))

        # Just for the sake of simplicity, as it is tolerable under Arch Linux and its kernel package handling,
        # kernel:install will be invoked for all existing kernels. But actually it would be sufficient to just
        # do it for the kernels listed in STDIN.
        for kernel_image_path in kernel_image_paths:
            kernel_name: str = kernel_image_path.replace(str(boot_path), '').split('-', 1)[1]

            self._forward('kernel', 'install', {'kernel_name': kernel_name})

        for stdin_line in sys.stdin:
            if stdin_line.rstrip() == 'systemd':
                self._forward('bootloader', 'update')

    def _pacman_remove_callback(self):
        # pacman outputs '/usr/lib/modules/<kernel_name>/vmlinuz' paths on STDIN for every removed kernel package.
        # The 'real' kernel_name as we need it can be found in /usr/lib/modules/<kernel_name>/pkgbase.
        for stdin_line in sys.stdin:
            kernel_pkgbase_file_path: Path = Path(stdin_line.rstrip()).parent / 'pkgbase'
            kernel_name: str = kernel_pkgbase_file_path.read_text().rstrip()

            self._forward('kernel', 'remove', {'kernel_name': kernel_name})

    def _apt_install(self):
        pm_name: str = self._config.package_manager_name
        hook_path: Path = Env.APP_HOOK_PATH / pm_name

        self._copy_hook_file(hook_path / 'initramfs' / 'yy-secbootctl-update', Path('/etc/initramfs/post-update.d'))
        self._copy_hook_file(hook_path / 'kernel' / 'yy-secbootctl-update', Path('/etc/kernel/postinst.d'))
        self._copy_hook_file(hook_path / 'kernel' / 'yy-secbootctl-remove', Path('/etc/kernel/postrm.d'))

    def _apt_remove(self):
        Path('/etc/initramfs/post-update.d/yy-secbootctl-update').unlink(missing_ok=True)
        Path('/etc/kernel/postinst.d/yy-secbootctl-update').unlink(missing_ok=True)
        Path('/etc/kernel/postrm.d/yy-secbootctl-remove').unlink(missing_ok=True)

    def _apt_update_callback(self, kernel_name: str):
        # @todo what to do with systemd-boot updates?
        self._forward('kernel', 'install', {'kernel_name': kernel_name})

    def _apt_remove_callback(self, kernel_name: str):
        self._forward('kernel', 'remove', {'kernel_name': kernel_name})

    def _copy_hook_file(self, hook_file_path: Path, target_hook_path: Path):
        if not target_hook_path.is_dir():
            os.makedirs(target_hook_path, 0o755, True)

        shutil.copy(hook_file_path, target_hook_path)
        copied_hook_file_path: Path = target_hook_path / hook_file_path.name
        shutil.chown(copied_hook_file_path, 'root', 'root')
        os.chmod(copied_hook_file_path, 0o700)


class PmiSubcmdCreator(BaseSubcmdCreator):
    def create(self, cli_subparsers):
        self._add(cli_subparsers, 'pmi:install', 'install package manager hook files', textwrap.dedent(f'''
            Install package manager hook files for configured package manager.

            The following package managers are currently supported: {', '.join(Env.SUPPORTED_PACKAGE_MANAGERS)}
        '''))
        self._add(cli_subparsers, 'pmi:remove', 'remove package manager hook files', textwrap.dedent(f'''
            Remove package manager hook files for configured package manager.

            The following package managers are currently supported: {', '.join(Env.SUPPORTED_PACKAGE_MANAGERS)}
        '''))
        pmc_cli_subparser = self._add(cli_subparsers, 'pmi:hook-callback', 'package manager hook callback',
                                      textwrap.dedent('''
            Callback for package manager hook. Gets invoked by the package manager hook itself.
        '''))
        pmc_cli_subparser.add_argument('mode', help='e.g. "update", "remove", etc.')
        pmc_cli_subparser.add_argument('kernel_name', nargs='?', help='e.g. "5.4.0-91-generic", etc.')
