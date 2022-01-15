import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import mock_open
from unittest.mock import patch

from secbootctl.core import AppError
from secbootctl.env import Env
from secbootctl.helpers.kernelos import KernelOsHelper


class TestKernelOsHelper(unittest.TestCase):
    def setUp(self) -> None:
        self._config_mock: Mock = Mock()
        self._path_mock: Mock = Mock()
        self._kernel_os_helper: KernelOsHelper = KernelOsHelper(self._config_mock)
        self._machine_id = '1234-5678'
        Env.MACHINE_ID = self._machine_id
        self._boot_path = Path('/boot')
        self._esp_path = Path('/boot/efi')
        self._config_mock.configure_mock(esp_path=self._esp_path)

    def test_init_it_assigns_key_file_paths(self):
        self.assertEqual(
            self._config_mock,
            self._kernel_os_helper._config
        )

    @patch('secbootctl.helpers.kernelos.Path')
    @patch('secbootctl.helpers.kernelos.os')
    def test_check_requirements_if_requirements_met_it_returns_none(self, os_patch_mock: MagicMock,
                                                                    path_patch_mock: MagicMock):
        os_patch_mock.getuid.return_value = 0
        path_patch_mock.return_value = self._path_mock
        self._path_mock.is_dir.return_value = True

        self.assertIsNone(
            self._kernel_os_helper.check_requirements()
        )

        path_patch_mock.assert_called_once_with(Env.EFI_BOOT_MODE_CHECK_PATH)

    @patch('secbootctl.helpers.kernelos.os')
    def test_check_requirements_if_no_root_it_raises_an_error(self, os_patch_mock: MagicMock):
        os_patch_mock.getuid.return_value = 1

        with self.assertRaises(AppError) as context_manager:
            self._kernel_os_helper.check_requirements()

        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            'root permissions required'
        )
        self.assertEqual(
            error.code,
            1
        )

    @patch('secbootctl.helpers.kernelos.Path')
    @patch('secbootctl.helpers.kernelos.os')
    def test_check_requirements_if_no_uefi_boot_mode_it_raises_an_error(self, os_patch_mock: MagicMock,
                                                                        path_patch_mock: MagicMock):
        os_patch_mock.getuid.return_value = 0
        path_patch_mock.return_value = self._path_mock
        self._path_mock.is_dir.return_value = False

        with self.assertRaises(AppError) as context_manager:
            self._kernel_os_helper.check_requirements()

        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            'UEFI boot mode required'
        )
        self.assertEqual(
            error.code,
            1
        )

    @patch('secbootctl.helpers.kernelos.subprocess')
    def test_build_unified_kernel_image_if_no_mc_and_no_error_it_builds_image(self, subprocess_patch_mock: MagicMock):
        kernel_name: str = 'linux-custom'
        kernel_image_name_prefix: str = 'vmlinuz'
        initramfs_image_name_template: str = 'initramfs__kernel-name__.img'
        microcode_image_name: str = 'microcode.img'
        unified_kernel_image_path: Path = Path('/tmp/image.efi')
        kernel_cmdline_file_path: Path = Path('/tmp/cmdline')
        kernel_cmdline_file_path_mock = MagicMock()
        kernel_cmdline_file_path_mock.is_file.return_value = True
        kernel_cmdline_file_path_mock.__str__.return_value = str(kernel_cmdline_file_path)
        Env.KERNEL_CMDLINE_ETC_FILE_PATH = kernel_cmdline_file_path_mock
        kernel_image_path = self._boot_path / (kernel_image_name_prefix + '-' + kernel_name)
        objcopy_initrd_image_path = self._boot_path / initramfs_image_name_template.replace(
            '__kernel-name__', kernel_name)
        self._config_mock.configure_mock(
            boot_path=self._boot_path,
            kernel_image_name_prefix=kernel_image_name_prefix,
            initramfs_image_name_template=initramfs_image_name_template,
            microcode_image_name=microcode_image_name,
            include_microcode=False
        )
        process_result_mock: Mock = Mock()
        subprocess_patch_mock.run.return_value = process_result_mock
        process_result_mock.configure_mock(returncode=0)

        self._kernel_os_helper.build_unified_kernel_image(kernel_name, unified_kernel_image_path)

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'objcopy',
                f'--add-section=.osrel={Env.OS_RELEASE_FILE_PATH}',
                '--change-section-vma=.osrel=0x20000',
                f'--add-section=.cmdline={kernel_cmdline_file_path}',
                '--change-section-vma=.cmdline=0x30000',
                f'--add-section=.linux={kernel_image_path}',
                '--change-section-vma=.linux=0x2000000',
                f'--add-section=.initrd={objcopy_initrd_image_path}',
                '--change-section-vma=.initrd=0x3000000',
                Env.BOOTLOADER_SYSTEMD_BOOT_STUB_FILE_PATH,
                unified_kernel_image_path
            ], capture_output=True
        )

    @patch('secbootctl.helpers.kernelos.subprocess')
    def test_build_unified_kernel_image_if_no_mc_and_error_it_raises_an_error(self, subprocess_patch_mock: MagicMock):
        kernel_name: str = 'linux-custom'
        kernel_image_name_prefix: str = 'vmlinuz'
        initramfs_image_name_template: str = 'initramfs__kernel-name__.img'
        microcode_image_name: str = 'microcode.img'
        unified_kernel_image_path: Path = Path('/tmp/image.efi')
        kernel_cmdline_file_path: Path = Path('/tmp/cmdline')
        kernel_cmdline_file_path_mock = MagicMock()
        kernel_cmdline_file_path_mock.is_file.return_value = True
        kernel_cmdline_file_path_mock.__str__.return_value = str(kernel_cmdline_file_path)
        Env.KERNEL_CMDLINE_ETC_FILE_PATH = kernel_cmdline_file_path_mock
        kernel_image_path = self._boot_path / (kernel_image_name_prefix + '-' + kernel_name)
        objcopy_initrd_image_path = self._boot_path / initramfs_image_name_template.replace(
            '__kernel-name__', kernel_name)
        self._config_mock.configure_mock(
            boot_path=self._boot_path,
            kernel_image_name_prefix=kernel_image_name_prefix,
            initramfs_image_name_template=initramfs_image_name_template,
            microcode_image_name=microcode_image_name,
            include_microcode=False
        )
        process_result_mock: Mock = Mock()
        subprocess_patch_mock.run.return_value = process_result_mock
        process_result_mock.configure_mock(returncode=1)

        with self.assertRaises(AppError) as context_manager:
            self._kernel_os_helper.build_unified_kernel_image(kernel_name, unified_kernel_image_path)

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'objcopy',
                f'--add-section=.osrel={Env.OS_RELEASE_FILE_PATH}',
                '--change-section-vma=.osrel=0x20000',
                f'--add-section=.cmdline={kernel_cmdline_file_path}',
                '--change-section-vma=.cmdline=0x30000',
                f'--add-section=.linux={kernel_image_path}',
                '--change-section-vma=.linux=0x2000000',
                f'--add-section=.initrd={objcopy_initrd_image_path}',
                '--change-section-vma=.initrd=0x3000000',
                Env.BOOTLOADER_SYSTEMD_BOOT_STUB_FILE_PATH,
                unified_kernel_image_path
            ], capture_output=True
        )
        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            f'building unified kernel image "{unified_kernel_image_path}" failed'
        )
        self.assertEqual(
            error.code,
            1
        )

    @patch('secbootctl.helpers.kernelos.shutil')
    @patch('secbootctl.helpers.kernelos.open', new_callable=mock_open())
    @patch('secbootctl.helpers.kernelos.subprocess')
    def test_build_unified_kernel_image_if_mc_and_no_error_it_builds_image(self, subprocess_patch_mock: MagicMock,
                                                                           open_patch_mock: MagicMock,
                                                                           shutil_patch_mock: MagicMock):
        kernel_name: str = 'linux-custom'
        kernel_image_name_prefix: str = 'vmlinuz'
        initramfs_image_name_template: str = 'initramfs__kernel-name__.img'
        microcode_image_name: str = 'microcode.img'
        unified_kernel_image_path: Path = Path('/tmp/image.efi')
        kernel_cmdline_file_path: Path = Path('/tmp/cmdline')
        kernel_cmdline_file_path_mock = MagicMock()
        kernel_cmdline_file_path_mock.is_file.return_value = True
        kernel_cmdline_file_path_mock.__str__.return_value = str(kernel_cmdline_file_path)
        Env.KERNEL_CMDLINE_ETC_FILE_PATH = kernel_cmdline_file_path_mock
        kernel_image_path: Path = self._boot_path / (kernel_image_name_prefix + '-' + kernel_name)
        initramfs_image_path: Path = self._boot_path / initramfs_image_name_template.replace(
            '__kernel-name__', kernel_name)
        microcode_image_path: Path = self._boot_path / microcode_image_name
        microcode_initramfs_unified_image_path: Path = self._boot_path / 'tmp-microcode-initramfs-unified.img'
        objcopy_initrd_image_path = microcode_initramfs_unified_image_path
        self._config_mock.configure_mock(
            boot_path=self._boot_path,
            kernel_image_name_prefix=kernel_image_name_prefix,
            initramfs_image_name_template=initramfs_image_name_template,
            microcode_image_name=microcode_image_name,
            include_microcode=True
        )
        process_result_mock: Mock = Mock()
        subprocess_patch_mock.run.return_value = process_result_mock
        process_result_mock.configure_mock(returncode=0)
        open_patch_mock.return_value = open_patch_mock
        combined_image_mock = mock_open()
        microcode_image_mock = mock_open()
        initramfs_image_mock = mock_open()
        open_patch_mock.__enter__.side_effect = [combined_image_mock, microcode_image_mock, initramfs_image_mock]

        self._kernel_os_helper.build_unified_kernel_image(kernel_name, unified_kernel_image_path)

        # @todo test open calls - did not find a way to test it correctly for all three open calls

        shutil_patch_mock.copyfileobj.assert_has_calls([
            call(microcode_image_mock, combined_image_mock),
            call(initramfs_image_mock, combined_image_mock)
        ])

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'objcopy',
                f'--add-section=.osrel={Env.OS_RELEASE_FILE_PATH}',
                '--change-section-vma=.osrel=0x20000',
                f'--add-section=.cmdline={kernel_cmdline_file_path}',
                '--change-section-vma=.cmdline=0x30000',
                f'--add-section=.linux={kernel_image_path}',
                '--change-section-vma=.linux=0x2000000',
                f'--add-section=.initrd={objcopy_initrd_image_path}',
                '--change-section-vma=.initrd=0x3000000',
                Env.BOOTLOADER_SYSTEMD_BOOT_STUB_FILE_PATH,
                unified_kernel_image_path
            ], capture_output=True
        )

    def test_get_default_kernel_name_if_not_latest_it_returns_configured_default_kernel_name(self):
        default_kernel_name: str = 'linux-custom'
        self._config_mock.configure_mock(default_kernel_name=default_kernel_name)

        self.assertEqual(
            default_kernel_name,
            self._kernel_os_helper.get_default_kernel_name()
        )

    @patch('secbootctl.helpers.kernelos.glob')
    def test_get_default_kernel_name_if_latest_it_returns_kernel_name_of_latest_kernel(self,
                                                                                       glob_patch_mock: MagicMock):
        kernel_image_name_prefix: str = 'vmlinuz'
        self._config_mock.configure_mock(
            boot_path=self._boot_path, default_kernel_name='latest', kernel_image_name_prefix=kernel_image_name_prefix
        )
        glob_patch_mock.glob.return_value = [
            f'{self._boot_path}/{kernel_image_name_prefix}-5.12.0.82-generic',
            f'{self._boot_path}/{kernel_image_name_prefix}-5.10.0.82-generic',
            f'{self._boot_path}/{kernel_image_name_prefix}-5.10.0.80-generic',
            f'{self._boot_path}/{kernel_image_name_prefix}-5.12.0.85-generic',
            f'{self._boot_path}/{kernel_image_name_prefix}-5.10.1.80-generic'
        ]

        self.assertEqual(
            '5.12.0.85-generic',
            self._kernel_os_helper.get_default_kernel_name()
        )

        glob_patch_mock.glob.assert_called_once_with(str(self._boot_path / (kernel_image_name_prefix + '-*')))

    @patch('secbootctl.helpers.kernelos.open', mock_open(read_data=f'ID=my-os-id'))
    def test_get_unified_kernel_image_path_it_returns_unified_kernel_image_path_for_given_kernel_name(self):
        kernel_name: str = 'linux-custom'

        self.assertEqual(
            self._esp_path / Env.UNIFIED_IMAGE_SUBPATH / (
                    Env.MACHINE_ID + '-' + kernel_name + '-my-os-id.efi'),
            self._kernel_os_helper.get_unified_kernel_image_path(kernel_name)
        )

    def test_get_kernel_version_if_pm_is_not_pacman_it_returns_given_kernel_name(self):
        kernel_name: str = '5.10.0.80-generic'
        self._config_mock.configure_mock(package_manager_name='apt')

        self.assertEqual(
            kernel_name,
            self._kernel_os_helper.get_kernel_version(kernel_name)
        )

    @patch('secbootctl.helpers.kernelos.subprocess')
    def test_get_kernel_version_if_pm_is_pacman_and_no_error_it_returns_version(self, subprocess_patch_mock: MagicMock):
        kernel_name: str = 'linux-custom'
        kernel_version: str = '5.15.0.1'
        self._config_mock.configure_mock(package_manager_name='pacman')
        process_result_mock: Mock = Mock()
        subprocess_patch_mock.run.return_value = process_result_mock
        stdout_mock: Mock = Mock()
        stdout_mock.decode.return_value = f'{kernel_name} {kernel_version}\n'
        process_result_mock.configure_mock(returncode=0, stdout=stdout_mock)

        self.assertEqual(
            kernel_version,
            self._kernel_os_helper.get_kernel_version(kernel_name)
        )

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'pacman',
                '-Q',
                kernel_name
            ], capture_output=True
        )

    @patch('secbootctl.helpers.kernelos.subprocess')
    def test_get_kernel_version_if_pm_is_pacman_but_error_it_raises_an_error(self, subprocess_patch_mock: MagicMock):
        kernel_name: str = 'linux-custom'
        self._config_mock.configure_mock(package_manager_name='pacman')
        process_result_mock: Mock = Mock()
        process_result_mock.configure_mock(returncode=1)

        with self.assertRaises(AppError) as context_manager:
            self._kernel_os_helper.get_kernel_version(kernel_name)

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'pacman',
                '-Q',
                kernel_name
            ], capture_output=True
        )
        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            f'could not resolve kernel version with pacman for kernel name "{kernel_name}"'
        )
        self.assertEqual(
            error.code,
            1
        )

    @patch('secbootctl.helpers.kernelos.open', mock_open(read_data=f'ANY=any\nID=my-os-id\nPRETTY_NAME=my-linux'))
    def test_get_os_id_it_returns_os_id(self):
        self.assertEqual(
            'my-os-id',
            self._kernel_os_helper.get_os_id()
        )

    @patch('secbootctl.helpers.kernelos.open', mock_open(read_data=f'ANY=any\nID=my-os-id\nPRETTY_NAME=my-linux'))
    def test_get_os_pretty_name_it_returns_os_pretty_name(self):
        self.assertEqual(
            'my-linux',
            self._kernel_os_helper.get_os_pretty_name()
        )


if __name__ == '__main__':
    unittest.main()
