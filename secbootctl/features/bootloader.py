# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

from secbootctl.core import AppController, AppError, BaseSubcmdCreator
from secbootctl.env import Env
from secbootctl.helpers.cli import CliPrintHelper


class BootloaderController(AppController):
    def install(self) -> None:
        self._install_systemd_boot()
        self._sign_systemd_boot_files()
        self._init_bootloader_config()

    def update(self) -> None:
        self._update_systemd_boot()
        self._sign_systemd_boot_files()

    def remove(self) -> None:
        self._remove_systemd_boot()

    def status(self) -> None:
        subprocess.run(['bootctl', 'status', f'--esp-path={self._config.esp_path}'])

    def update_menu(self) -> None:
        """Updates default bootloader menu entry file "<esp_path>/loader/entries/secbootctl-default-linux.conf".

        Sets the configured default kernel (see configuration file) as default bootloader menu entry.

        see https://systemd.io/BOOT_LOADER_SPECIFICATION/
        """
        default_kernel_name: str = self._kernel_os_helper.get_default_kernel_name()
        default_unified_image_path: Path = self._kernel_os_helper.get_unified_kernel_image_path(default_kernel_name)
        esp_path: Path = self._config.esp_path
        default_unified_kernel_image_subpath: str = str(default_unified_image_path).replace(str(esp_path), '')
        default_entry_file_path: Path = esp_path / Env.BOOTLOADER_DEFAULT_ENTRY_FILE_SUBPATH

        self._print_status(f'updating default bootloader entry: {default_entry_file_path}')

        if not default_unified_image_path.is_file():
            raise AppError(f'unified kernel image "{default_unified_image_path}" for default kernel not found')

        entry_content: str = textwrap.dedent(f'''
            title {self._kernel_os_helper.get_os_pretty_name()}
            machine-id {Env.MACHINE_ID}
            version {self._kernel_os_helper.get_kernel_version(default_kernel_name)}
            linux {default_unified_kernel_image_subpath}
        ''')

        with open(default_entry_file_path, 'w') as file:
            file.write(entry_content)

        self._print_status(f'updated default bootloader entry: {default_entry_file_path}',
                           CliPrintHelper.Status.SUCCESS)

    def _install_systemd_boot(self) -> None:
        self._print_status('installing bootloader: systemd-boot')

        process_result = subprocess.run(
            ['bootctl', 'install', f'--esp-path={self._config.esp_path}'], capture_output=True
        )

        if process_result.returncode != 0:
            raise AppError('installing bootloader systemd-boot failed')

        self._print_status('installed bootloader: systemd-boot', CliPrintHelper.Status.SUCCESS)

    def _update_systemd_boot(self) -> None:
        self._print_status('updating bootloader: systemd-boot')

        process_result = subprocess.run(
            ['bootctl', 'update', f'--esp-path={self._config.esp_path}'], capture_output=True
        )

        # I'm not sure why systemd handles skipping, when files are same, as an error but for us skipping is alright.
        # @todo Using regex might be a bit prettier. Currently this could lead to false success because there could
        # be other 'Skipping' errors too?!
        if process_result.returncode != 0 \
                and process_result.stderr.find(b'Skipping') == -1 \
                and process_result.stderr.find(b'since same boot loader version in place already') == -1:
            raise AppError('updating bootloader systemd-boot failed')

        self._print_status('updated bootloader: systemd-boot', CliPrintHelper.Status.SUCCESS)

    def _remove_systemd_boot(self) -> None:
        self._print_status('removing bootloader: systemd-boot')

        process_result = subprocess.run(
            ['bootctl', 'remove', f'--esp-path={self._config.esp_path}'], capture_output=True
        )

        if process_result.returncode != 0:
            raise AppError('removing bootloader systemd-boot failed')

        self._print_status('removed bootloader: systemd-boot', CliPrintHelper.Status.SUCCESS)

    def _sign_systemd_boot_files(self) -> None:
        esp_path: Path = self._config.esp_path
        default_boot_file_path: Path = esp_path / Env.BOOTLOADER_DEFAULT_BOOT_FILE_SUBPATH
        systemd_boot_file_path: Path = esp_path / Env.BOOTLOADER_SYSTEMD_BOOT_BOOT_FILE_SUBPATH

        self._sign_file(default_boot_file_path)
        self._sign_file(systemd_boot_file_path)
        self._verify_file(default_boot_file_path)
        self._verify_file(systemd_boot_file_path)

    def _init_bootloader_config(self) -> None:
        """Initializes "<esp_path>/loader/loader.conf" by setting default entry file name, timeout, etc.

        see https://www.freedesktop.org/software/systemd/man/loader.conf.html
        """
        config_file_path: Path = self._config.esp_path / Env.BOOTLOADER_CONFIG_FILE_SUBPATH
        config_content: str = textwrap.dedent(f'''
            default {Env.BOOTLOADER_DEFAULT_ENTRY_FILE_NAME}
            editor {self._config.bootloader_menu_editor}
            timeout {self._config.bootloader_menu_timeout}
        ''')

        self._print_status(f'initializing bootloader config file: {config_file_path}')

        with open(config_file_path, 'w') as file:
            file.write(config_content)

        self._print_status(f'initialized bootloader config file: {config_file_path}', CliPrintHelper.Status.SUCCESS)


class BootloaderSubcmdCreator(BaseSubcmdCreator):
    def create(self, cli_subparsers):
        self._add(cli_subparsers, 'bootloader:install', 'install bootloader (systemd-boot)', textwrap.dedent(f'''
            Install the bootloader on the EFI System Partition (ESP). Currently
            the bootloader is always systemd-boot.

            The following steps will be performed:
                - calling the systemd command "bootctl install"
                - initializing the bootloader config file "{self._esp_path}/{Env.BOOTLOADER_CONFIG_FILE_SUBPATH}"
                - signing the bootloader files on the EFI System Partition (ESP)
        '''))
        self._add(cli_subparsers, 'bootloader:update', 'update bootloader (systemd-boot)', textwrap.dedent('''
            Update the bootloader on the EFI System Partition (ESP). Currently
            the bootloader is always systemd-boot.

            The following steps will be performed:
                - calling the systemd command "bootctl update"
                - signing the bootloader files on the EFI System Partition (ESP)
        '''))
        self._add(cli_subparsers, 'bootloader:remove', 'remove bootloader (systemd-boot)', textwrap.dedent('''
            Remove the bootloader on the EFI System Partition (ESP). Currently
            the bootloader is always systemd-boot.

            The following step will be performed:
                - calling the systemd command "bootctl remove"
        '''))
        self._add(cli_subparsers, 'bootloader:status', 'show bootloader status (systemd-boot)', textwrap.dedent('''
            Print the bootloader status. Currently the bootloader is always systemd-boot.

            The following step will be performed:
                - calling the systemd command "bootctl status"
        '''))
        self._add(cli_subparsers, 'bootloader:update-menu', 'update bootloader menu', textwrap.dedent(f'''
            Update the bootloader menu. Currently the bootloader is always systemd-boot.
            Actually just sets the default configured kernel as default menu entry as
            the unified kernel images in "{self._esp_path}/{Env.UNIFIED_IMAGE_SUBPATH}" are automatically
            detected and added to the bootloader menu by systemd-boot.

            The following step will be performed:
                - updating "{self._esp_path}/{Env.BOOTLOADER_DEFAULT_ENTRY_FILE_SUBPATH}"
        '''))
