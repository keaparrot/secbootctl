import unittest
from pathlib import Path
from unittest.mock import call
from unittest.mock import Mock
from unittest.mock import MagicMock
from unittest.mock import patch

from secbootctl.helpers.cli import CliPrintHelper
from tests import unittest_helper


# @todo install - add tests for errors if signing or verification fails
class TestKernelController(unittest_helper.ControllerTestCase):
    FEATURE_NAME: str = 'kernel'

    def test_install_if_kernel_name_given_it_installs_unified_image(self):
        kernel_name: str = 'linux-custom'
        unified_kernel_image_path: Path = Path('/tmp/EFI/Linux/linux-custom.efi')
        self._kernel_os_helper_mock.get_unified_kernel_image_path.return_value = unified_kernel_image_path
        self._sb_helper_mock.sign_file.return_value = True
        self._sb_helper_mock.verify_file.return_value = True

        self._controller.install(kernel_name)

        self._kernel_os_helper_mock.get_unified_kernel_image_path.assert_called_once_with(
            kernel_name
        )
        self._kernel_os_helper_mock.build_unified_kernel_image.assert_called_once_with(
            kernel_name, unified_kernel_image_path
        )
        self._sb_helper_mock.sign_file.assert_called_once_with(
            unified_kernel_image_path
        )
        self._sb_helper_mock.verify_file.assert_called_once_with(
            unified_kernel_image_path
        )
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'building unified kernel image: {unified_kernel_image_path}', CliPrintHelper.Status.PENDING),
            call(f'built unified kernel image: {unified_kernel_image_path}', CliPrintHelper.Status.SUCCESS),
            call(f'signing: {unified_kernel_image_path}', CliPrintHelper.Status.PENDING),
            call(f'signed: {unified_kernel_image_path}', CliPrintHelper.Status.SUCCESS),
            call(f'verifying signature: {unified_kernel_image_path}', CliPrintHelper.Status.PENDING),
            call(f'valid signature: {unified_kernel_image_path}', CliPrintHelper.Status.SUCCESS)
        ])

    def test_install_if_kernel_name_not_given_it_installs_default_unified_image(self):
        kernel_name: str = 'linux-custom'
        self._kernel_os_helper_mock.get_default_kernel_name.return_value = kernel_name
        unified_kernel_image_path: Path = Path('/tmp/EFI/Linux/linux-custom.efi')
        self._kernel_os_helper_mock.get_unified_kernel_image_path.return_value = unified_kernel_image_path
        self._sb_helper_mock.sign_file.return_value = True
        self._sb_helper_mock.verify_file.return_value = True

        self._controller.install()

        self._kernel_os_helper_mock.get_default_kernel_name.assert_called_once()
        self._kernel_os_helper_mock.get_unified_kernel_image_path.assert_called_once_with(
            kernel_name
        )
        self._kernel_os_helper_mock.build_unified_kernel_image.assert_called_once_with(
            kernel_name, unified_kernel_image_path
        )
        self._sb_helper_mock.sign_file.assert_called_once_with(
            unified_kernel_image_path
        )
        self._sb_helper_mock.verify_file.assert_called_once_with(
            unified_kernel_image_path
        )
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'building unified kernel image: {unified_kernel_image_path}', CliPrintHelper.Status.PENDING),
            call(f'built unified kernel image: {unified_kernel_image_path}', CliPrintHelper.Status.SUCCESS),
            call(f'signing: {unified_kernel_image_path}', CliPrintHelper.Status.PENDING),
            call(f'signed: {unified_kernel_image_path}', CliPrintHelper.Status.SUCCESS),
            call(f'verifying signature: {unified_kernel_image_path}', CliPrintHelper.Status.PENDING),
            call(f'valid signature: {unified_kernel_image_path}', CliPrintHelper.Status.SUCCESS)
        ])

    @patch('secbootctl.features.kernel.Path')
    def test_remove_if_kernel_name_given_it_removes_unified_image(self, path_patch_mock: MagicMock):
        kernel_name: str = 'linux-custom'
        path_mock: Mock = Mock()
        path_patch_mock.return_value = path_mock
        unified_kernel_image_path: Path = path_mock
        self._kernel_os_helper_mock.get_unified_kernel_image_path.return_value = unified_kernel_image_path

        self._controller.remove(kernel_name)

        self._kernel_os_helper_mock.get_unified_kernel_image_path.assert_called_once_with(
            kernel_name
        )
        path_mock.unlink.assert_called_once_with(
            missing_ok=True
        )
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'removing unified kernel image: {unified_kernel_image_path}', CliPrintHelper.Status.PENDING),
            call(f'removed unified kernel image: {unified_kernel_image_path}', CliPrintHelper.Status.SUCCESS)
        ])

    @patch('secbootctl.features.kernel.Path')
    def test_remove_if_kernel_name_not_given_it_removes_default_unified_image(self, path_patch_mock: MagicMock):
        kernel_name: str = 'linux-default'
        self._kernel_os_helper_mock.get_default_kernel_name.return_value = kernel_name
        path_mock: Mock = Mock()
        path_patch_mock.return_value = path_mock
        unified_kernel_image_path: Path = path_mock
        self._kernel_os_helper_mock.get_unified_kernel_image_path.return_value = unified_kernel_image_path

        self._controller.remove()

        self._kernel_os_helper_mock.get_default_kernel_name.assert_called_once()
        self._kernel_os_helper_mock.get_unified_kernel_image_path.assert_called_once_with(
            kernel_name
        )
        path_mock.unlink.assert_called_once_with(
            missing_ok=True
        )
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'removing unified kernel image: {unified_kernel_image_path}', CliPrintHelper.Status.PENDING),
            call(f'removed unified kernel image: {unified_kernel_image_path}', CliPrintHelper.Status.SUCCESS)
        ])


if __name__ == '__main__':
    unittest.main()
