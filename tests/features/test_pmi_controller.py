import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

from secbootctl.core import AppError
from secbootctl.env import Env
from secbootctl.helpers.cli import CliPrintHelper
from tests import unittest_helper


class TestPmiController(unittest_helper.ControllerTestCase):
    FEATURE_NAME: str = 'pmi'

    @patch('secbootctl.features.pmi.os')
    @patch('secbootctl.features.pmi.shutil')
    @patch('secbootctl.features.pmi.glob')
    def test_install_if_supported_it_installs_hook_files(self, glob_patch_mock: MagicMock, shutil_patch_mock: MagicMock,
                                                         os_patch_mock: MagicMock):
        pm_name = 'pacman'
        hook_path: Path = Env.APP_HOOK_PATH / pm_name
        hook_target_path: Path = Path('/etc/pacman.d/hooks')
        self._config_mock.configure_mock(package_manager_name=pm_name)
        glob_patch_mock.glob.return_value = [
            f'{hook_path}/update-hook.hook',
            f'{hook_path}/remove-hook.hook'
        ]

        self._controller.install()

        glob_patch_mock.glob.assert_called_once_with(
            str(hook_path / '*.*')
        )
        shutil_patch_mock.copy.assert_has_calls([
            call(hook_path / 'update-hook.hook', hook_target_path),
            call(hook_path / 'remove-hook.hook', hook_target_path)
        ])
        shutil_patch_mock.chown.assert_has_calls([
            call(hook_target_path / 'update-hook.hook', 'root', 'root'),
            call(hook_target_path / 'remove-hook.hook', 'root', 'root')
        ])
        os_patch_mock.chmod.assert_has_calls([
            call(hook_target_path / 'update-hook.hook', 0o700),
            call(hook_target_path / 'remove-hook.hook', 0o700)
        ])
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'installing hook files for package manager: {pm_name}', CliPrintHelper.Status.PENDING),
            call(f'installed hook files for package manager: {pm_name}', CliPrintHelper.Status.SUCCESS)
        ])

    def test_install_if_not_supported_it_raises_an_error(self):
        pm_name = 'unknown'
        self._config_mock.configure_mock(package_manager_name=pm_name)

        with self.assertRaises(AppError) as context_manager:
            self._controller.install()

        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            f'configured package manager "{pm_name}" is not supported'
        )
        self.assertEqual(
            error.code,
            1
        )

    @patch('secbootctl.features.pmi.Path.unlink')
    @patch('secbootctl.features.pmi.glob')
    def test_remove_if_supported_it_removes_hook_files(self, glob_patch_mock: MagicMock,
                                                       path_unlink_patch_mock: MagicMock):
        pm_name = 'pacman'
        hook_path: Path = Env.APP_HOOK_PATH / pm_name
        hook_target_path: Path = Path('/etc/pacman.d/hooks')
        self._config_mock.configure_mock(package_manager_name=pm_name)
        glob_patch_mock.glob.return_value = [
            f'{hook_path}/update-hook.hook',
            f'{hook_path}/remove-hook.hook'
        ]

        self._controller.remove()

        glob_patch_mock.glob.assert_called_once_with(
            str(hook_path / '*.*')
        )
        path_unlink_patch_mock.assert_called_with(missing_ok=True)
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'removing hook files for package manager: {pm_name}', CliPrintHelper.Status.PENDING),
            call(f'removed hook files for package manager: {pm_name}', CliPrintHelper.Status.SUCCESS)
        ])

    @patch('secbootctl.features.pmi.glob')
    def test_remove_if_not_supported_it_raises_an_error(self, glob_patch_mock: MagicMock):
        pm_name = 'unknown'
        self._config_mock.configure_mock(package_manager_name=pm_name)

        with self.assertRaises(AppError) as context_manager:
            self._controller.remove()

        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            f'configured package manager "{pm_name}" is not supported'
        )
        self.assertEqual(
            error.code,
            1
        )

    @patch('sys.stdin', StringIO('linux'))
    @patch('secbootctl.features.pmi.glob')
    def test_hook_callback_pacman_update_if_supported_and_no_systemd_update_it_signs_all_kernels(self, glob_patch_mock: MagicMock):
        pm_name = 'pacman'
        boot_path: Path = Path('/boot')
        kernel_image_name_prefix: str = 'vmlinuz'
        self._config_mock.configure_mock(
            boot_path=boot_path, kernel_image_name_prefix=kernel_image_name_prefix, package_manager_name=pm_name
        )
        glob_patch_mock.glob.return_value = [
            f'{boot_path}/{kernel_image_name_prefix}-linux',
            f'{boot_path}/{kernel_image_name_prefix}-linux-lts',
            f'{boot_path}/{kernel_image_name_prefix}-5.10.0.14-generic',
        ]

        self._controller.hook_callback('update')

        glob_patch_mock.glob.assert_called_once_with(
            str(boot_path / (kernel_image_name_prefix + '-*'))
        )
        self._dispatcher_mock.dispatch.assert_has_calls([
            call({
                'module_name': 'secbootctl.features.kernel',
                'controller_name': 'KernelController',
                'action_name': 'install',
                'params': {'kernel_name': 'linux'}
            }),
            call({
                'module_name': 'secbootctl.features.kernel',
                'controller_name': 'KernelController',
                'action_name': 'install',
                'params': {'kernel_name': 'linux-lts'}
            }),
            call({
                'module_name': 'secbootctl.features.kernel',
                'controller_name': 'KernelController',
                'action_name': 'install',
                'params': {'kernel_name': '5.10.0.14-generic'}
            }),
        ])

    @patch('sys.stdin', StringIO('linux\nsystemd'))
    @patch('secbootctl.features.pmi.glob')
    def test_hook_callback_pacman_update_if_supported_and_systemd_update_it_signs_all_kernels_and_updates_bootloader(self, glob_patch_mock: MagicMock):
        pm_name = 'pacman'
        boot_path: Path = Path('/boot')
        kernel_image_name_prefix: str = 'vmlinuz'
        self._config_mock.configure_mock(
            boot_path=boot_path, kernel_image_name_prefix=kernel_image_name_prefix, package_manager_name=pm_name
        )
        glob_patch_mock.glob.return_value = [
            f'{boot_path}/{kernel_image_name_prefix}-linux',
            f'{boot_path}/{kernel_image_name_prefix}-linux-lts',
            f'{boot_path}/{kernel_image_name_prefix}-5.10.0.14-generic',
        ]

        self._controller.hook_callback('update')

        glob_patch_mock.glob.assert_called_once_with(
            str(boot_path / (kernel_image_name_prefix + '-*'))
        )
        self._dispatcher_mock.dispatch.assert_has_calls([
            call({
                'module_name': 'secbootctl.features.kernel',
                'controller_name': 'KernelController',
                'action_name': 'install',
                'params': {'kernel_name': 'linux'}
            }),
            call({
                'module_name': 'secbootctl.features.kernel',
                'controller_name': 'KernelController',
                'action_name': 'install',
                'params': {'kernel_name': 'linux-lts'}
            }),
            call({
                'module_name': 'secbootctl.features.kernel',
                'controller_name': 'KernelController',
                'action_name': 'install',
                'params': {'kernel_name': '5.10.0.14-generic'}
            }),
            call({
                'module_name': 'secbootctl.features.bootloader',
                'controller_name': 'BootloaderController',
                'action_name': 'update',
                'params': {}
            })
        ])

    def test_hook_callback_pacman_update_if_not_supported_it_raises_an_error(self):
        pm_name = 'unknown'
        self._config_mock.configure_mock(package_manager_name=pm_name)

        with self.assertRaises(AppError) as context_manager:
            self._controller.hook_callback('update')

        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            f'configured package manager "{pm_name}" is not supported'
        )
        self.assertEqual(
            error.code,
            1
        )

    @patch('sys.stdin', StringIO('/usr/lib/modules/5.15.8/vmlinuz\n/usr/lib/modules/5.10.85-lts/vmlinuz'))
    @patch('secbootctl.features.pmi.Path.read_text')
    def test_hook_callback_pacman_remove_if_supported_it_removes_given_kernels(self, path_read_text_patch_mock: MagicMock):
        pm_name = 'pacman'
        self._config_mock.configure_mock(package_manager_name=pm_name)
        path_read_text_patch_mock.side_effect = ['linux', 'linux-lts']

        self._controller.hook_callback('remove')

        self._dispatcher_mock.dispatch.assert_has_calls([
            call({
                'module_name': 'secbootctl.features.kernel',
                'controller_name': 'KernelController',
                'action_name': 'remove',
                'params': {'kernel_name': 'linux'}
            }),
            call({
                'module_name': 'secbootctl.features.kernel',
                'controller_name': 'KernelController',
                'action_name': 'remove',
                'params': {'kernel_name': 'linux-lts'}
            })
        ])

    def test_hook_callback_pacman_remove_if_not_supported_it_raises_an_error(self):
        pm_name = 'unknown'
        self._config_mock.configure_mock(package_manager_name=pm_name)

        with self.assertRaises(AppError) as context_manager:
            self._controller.hook_callback('remove')

        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            f'configured package manager "{pm_name}" is not supported'
        )
        self.assertEqual(
            error.code,
            1
        )


if __name__ == '__main__':
    unittest.main()
