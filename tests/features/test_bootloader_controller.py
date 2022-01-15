import textwrap
import unittest
from pathlib import Path
from unittest.mock import call
from unittest.mock import mock_open
from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import patch

from secbootctl.core import AppError
from secbootctl.env import Env
from secbootctl.helpers.cli import CliPrintHelper
from tests import unittest_helper


# @todo install/update - add tests for errors if signing or verification fails
class TestKernelController(unittest_helper.ControllerTestCase):
    FEATURE_NAME: str = 'bootloader'

    @patch('secbootctl.features.bootloader.open', new_callable=mock_open())
    @patch('secbootctl.features.bootloader.subprocess')
    def test_install_it_installs_bootloader(self, subprocess_patch_mock: MagicMock, open_patch_mock: MagicMock):
        process_result_mock: Mock = Mock()
        subprocess_patch_mock.run.return_value = process_result_mock
        process_result_mock.configure_mock(returncode=0)
        esp_path: Path = Path('/tmp/efi')
        bootloader_menu_editor: str = 'yes'
        bootloader_menu_timeout: int = 9
        self._config_mock.configure_mock(
            esp_path=esp_path,
            bootloader_menu_editor=bootloader_menu_editor,
            bootloader_menu_timeout=bootloader_menu_timeout
        )
        self._sb_helper_mock.sign_file.return_value = True
        self._sb_helper_mock.verify_file.return_value = True
        default_boot_file_path: Path = esp_path / Env.BOOTLOADER_DEFAULT_BOOT_FILE_SUBPATH
        systemd_boot_file_path: Path = esp_path / Env.BOOTLOADER_SYSTEMD_BOOT_BOOT_FILE_SUBPATH
        config_file_path: Path = esp_path / Env.BOOTLOADER_CONFIG_FILE_SUBPATH
        config_content: str = textwrap.dedent(f'''
            default {Env.BOOTLOADER_DEFAULT_ENTRY_FILE_NAME}
            editor {bootloader_menu_editor}
            timeout {bootloader_menu_timeout}
        ''')
        file_mock: Mock = MagicMock()
        open_patch_mock.return_value = file_mock

        self._controller.install()

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'bootctl',
                'install',
                f'--esp-path={esp_path}'
            ],
            capture_output=True
        )
        self._sb_helper_mock.sign_file.assert_has_calls([
            call(default_boot_file_path),
            call(systemd_boot_file_path)
        ])
        self._sb_helper_mock.verify_file.assert_has_calls([
            call(default_boot_file_path),
            call(systemd_boot_file_path)
        ])
        open_patch_mock.assert_called_once_with(config_file_path, 'w')
        file_mock.__enter__.return_value.write.assert_called_once_with(config_content)
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call('installing bootloader: systemd-boot', CliPrintHelper.Status.PENDING),
            call('installed bootloader: systemd-boot', CliPrintHelper.Status.SUCCESS),
            call(f'signing: {default_boot_file_path}', CliPrintHelper.Status.PENDING),
            call(f'signed: {default_boot_file_path}', CliPrintHelper.Status.SUCCESS),
            call(f'signing: {systemd_boot_file_path}', CliPrintHelper.Status.PENDING),
            call(f'signed: {systemd_boot_file_path}', CliPrintHelper.Status.SUCCESS),
            call(f'verifying signature: {default_boot_file_path}', CliPrintHelper.Status.PENDING),
            call(f'valid signature: {default_boot_file_path}', CliPrintHelper.Status.SUCCESS),
            call(f'verifying signature: {systemd_boot_file_path}', CliPrintHelper.Status.PENDING),
            call(f'valid signature: {systemd_boot_file_path}', CliPrintHelper.Status.SUCCESS)
        ])

    @patch('secbootctl.features.bootloader.subprocess')
    def test_install_if_fails_it_raises_an_error(self, subprocess_patch_mock: MagicMock):
        process_result_mock: Mock = Mock()
        subprocess_patch_mock.run.return_value = process_result_mock
        process_result_mock.configure_mock(returncode=1)
        esp_path: Path = Path('/tmp/efi')
        self._config_mock.configure_mock(esp_path=esp_path)

        with self.assertRaises(AppError) as context_manager:
            self._controller.install()

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'bootctl',
                'install',
                f'--esp-path={esp_path}'
            ],
            capture_output=True
        )
        self._cli_print_helper_mock.print_status.assert_called_once_with(
            'installing bootloader: systemd-boot', CliPrintHelper.Status.PENDING
        )
        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            'installing bootloader systemd-boot failed'
        )
        self.assertEqual(
            error.code,
            1
        )

    @patch('secbootctl.features.bootloader.subprocess')
    def test_update_it_updates_bootloader(self, subprocess_patch_mock: MagicMock):
        process_result_mock: Mock = Mock()
        subprocess_patch_mock.run.return_value = process_result_mock
        process_result_mock.configure_mock(returncode=0)
        esp_path: Path = Path('/tmp/efi')
        self._config_mock.configure_mock(esp_path=esp_path)
        self._sb_helper_mock.sign_file.return_value = True
        self._sb_helper_mock.verify_file.return_value = True
        default_boot_file_path: Path = esp_path / Env.BOOTLOADER_DEFAULT_BOOT_FILE_SUBPATH
        systemd_boot_file_path: Path = esp_path / Env.BOOTLOADER_SYSTEMD_BOOT_BOOT_FILE_SUBPATH

        self._controller.update()

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'bootctl',
                'update',
                f'--esp-path={esp_path}'
            ],
            capture_output=True
        )
        self._sb_helper_mock.sign_file.assert_has_calls([
            call(default_boot_file_path),
            call(systemd_boot_file_path)
        ])
        self._sb_helper_mock.verify_file.assert_has_calls([
            call(default_boot_file_path),
            call(systemd_boot_file_path)
        ])
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call('updating bootloader: systemd-boot', CliPrintHelper.Status.PENDING),
            call('updated bootloader: systemd-boot', CliPrintHelper.Status.SUCCESS),
            call(f'signing: {default_boot_file_path}', CliPrintHelper.Status.PENDING),
            call(f'signed: {default_boot_file_path}', CliPrintHelper.Status.SUCCESS),
            call(f'signing: {systemd_boot_file_path}', CliPrintHelper.Status.PENDING),
            call(f'signed: {systemd_boot_file_path}', CliPrintHelper.Status.SUCCESS),
            call(f'verifying signature: {default_boot_file_path}', CliPrintHelper.Status.PENDING),
            call(f'valid signature: {default_boot_file_path}', CliPrintHelper.Status.SUCCESS),
            call(f'verifying signature: {systemd_boot_file_path}', CliPrintHelper.Status.PENDING),
            call(f'valid signature: {systemd_boot_file_path}', CliPrintHelper.Status.SUCCESS)
        ])

    @patch('secbootctl.features.bootloader.subprocess')
    def test_update_if_fails_it_raises_an_error(self, subprocess_patch_mock: MagicMock):
        process_result_mock: Mock = Mock()
        subprocess_patch_mock.run.return_value = process_result_mock
        process_result_mock.configure_mock(returncode=1,stderr=b'failed')
        esp_path: Path = Path('/tmp/efi')
        self._config_mock.configure_mock(esp_path=esp_path)

        with self.assertRaises(AppError) as context_manager:
            self._controller.update()

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'bootctl',
                'update',
                f'--esp-path={esp_path}'
            ],
            capture_output=True
        )
        self._cli_print_helper_mock.print_status.assert_called_once_with(
            'updating bootloader: systemd-boot', CliPrintHelper.Status.PENDING
        )
        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            'updating bootloader systemd-boot failed'
        )
        self.assertEqual(
            error.code,
            1
        )

    @patch('secbootctl.features.bootloader.subprocess')
    def test_remove_it_removes_bootloader(self, subprocess_patch_mock: MagicMock):
        process_result_mock: Mock = Mock()
        subprocess_patch_mock.run.return_value = process_result_mock
        process_result_mock.configure_mock(returncode=0)
        esp_path: Path = Path('/tmp/efi')
        self._config_mock.configure_mock(esp_path=esp_path)

        self._controller.remove()

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'bootctl',
                'remove',
                f'--esp-path={esp_path}'
            ],
            capture_output=True
        )
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call('removing bootloader: systemd-boot', CliPrintHelper.Status.PENDING),
            call('removed bootloader: systemd-boot', CliPrintHelper.Status.SUCCESS)
        ])

    @patch('secbootctl.features.bootloader.subprocess')
    def test_remove_if_fails_it_raises_an_error(self, subprocess_patch_mock: MagicMock):
        process_result_mock: Mock = Mock()
        subprocess_patch_mock.run.return_value = process_result_mock
        process_result_mock.configure_mock(returncode=1)
        esp_path: Path = Path('/tmp/efi')
        self._config_mock.configure_mock(esp_path=esp_path)

        with self.assertRaises(AppError) as context_manager:
            self._controller.remove()

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'bootctl',
                'remove',
                f'--esp-path={esp_path}'
            ],
            capture_output=True
        )
        self._cli_print_helper_mock.print_status.assert_called_once_with(
            'removing bootloader: systemd-boot', CliPrintHelper.Status.PENDING
        )
        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            'removing bootloader systemd-boot failed'
        )
        self.assertEqual(
            error.code,
            1
        )

    @patch('secbootctl.features.bootloader.subprocess')
    def test_status_it_prints_status(self, subprocess_patch_mock: MagicMock):
        esp_path: Path = Path('/tmp/efi')
        self._config_mock.configure_mock(esp_path=esp_path)

        self._controller.status()

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'bootctl',
                'status',
                f'--esp-path={esp_path}'
            ]
        )

    @patch('secbootctl.features.bootloader.Path.is_file')
    @patch('secbootctl.features.bootloader.open', new_callable=mock_open())
    def test_update_menu_it_updates_default_menu_entry(self, open_patch_mock: MagicMock,
                                                       path_is_file_path_mock: MagicMock):
        default_kernel_name: str = 'linux-custom'
        default_unified_kernel_image_path: Path = Path('/tmp/EFI/Linux/linux-custom.efi')
        self._kernel_os_helper_mock.get_default_kernel_name.return_value = default_kernel_name
        self._kernel_os_helper_mock.get_unified_kernel_image_path.return_value = default_unified_kernel_image_path
        esp_path: Path = Path('/tmp/efi')
        self._config_mock.configure_mock(esp_path=esp_path)
        default_entry_file_path: Path = esp_path / Env.BOOTLOADER_DEFAULT_ENTRY_FILE_SUBPATH
        default_unified_kernel_image_subpath: str = str(default_unified_kernel_image_path).replace(str(esp_path), '')
        machine_id: str = '1234'
        Env.MACHINE_ID = machine_id
        os_pretty_name: str = 'PrettyLinux'
        kernel_version: str = '5.18'
        self._kernel_os_helper_mock.get_os_pretty_name.return_value = os_pretty_name
        self._kernel_os_helper_mock.get_kernel_version.return_value = kernel_version
        path_is_file_path_mock.return_value = True
        file_mock: Mock = MagicMock()
        open_patch_mock.return_value = file_mock
        entry_content: str = textwrap.dedent(f'''
            title {os_pretty_name}
            machine-id {machine_id}
            version {kernel_version}
            linux {default_unified_kernel_image_subpath}
        ''')

        self._controller.update_menu()

        self._kernel_os_helper_mock.get_default_kernel_name.assert_called_once()
        self._kernel_os_helper_mock.get_unified_kernel_image_path.assert_called_once_with(
            default_kernel_name
        )
        self._kernel_os_helper_mock.get_os_pretty_name.assert_called_once()
        self._kernel_os_helper_mock.get_kernel_version.assert_called_once_with(
            default_kernel_name
        )
        open_patch_mock.assert_called_once_with(default_entry_file_path, 'w')
        file_mock.__enter__.return_value.write.assert_called_once_with(entry_content)
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'updating default bootloader entry: {default_entry_file_path}', CliPrintHelper.Status.PENDING),
            call(f'updated default bootloader entry: {default_entry_file_path}', CliPrintHelper.Status.SUCCESS)
        ])


if __name__ == '__main__':
    unittest.main()
