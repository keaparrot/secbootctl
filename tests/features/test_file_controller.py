import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

from secbootctl.core import AppError
from secbootctl.helpers.cli import CliPrintHelper
from tests import unittest_helper


class TestFileController(unittest_helper.ControllerTestCase):
    FEATURE_NAME: str = 'file'

    @patch('sys.stdout', new_callable=StringIO)
    @patch('secbootctl.features.file.Path.is_dir')
    @patch('secbootctl.features.file.glob')
    def test_list_if_not_all_it_lists_only_efi_files(self, glob_patch_mock: MagicMock, path_is_dir_patch_mock,
                                                     stdout_mock: MagicMock):
        esp_path = Path('/boot/efi')
        self._config_mock.configure_mock(esp_path=esp_path)
        glob_patch_mock.glob.side_effect = [
            [
                f'{esp_path}/EFI/Linux/test.efi',
                f'{esp_path}/EFI/Linux/test2.efi',
                f'{esp_path}/test3.efi'
            ],
            [
                f'{esp_path}/EFI/BOOT/boot.EFI',
            ]
        ]
        path_is_dir_patch_mock.return_value = False
        self._sb_helper_mock.verify_file.side_effect = [True, False, True, True]

        self._controller.list(False)

        glob_patch_mock.glob.assert_has_calls([
            call(str(esp_path / '**' / '*.efi'), recursive=True),
            call(str(esp_path / '**' / '*.EFI'), recursive=True)
        ])

        self.assertEqual(f'''{esp_path}/EFI/BOOT/boot.EFI
{"Status":>10} \u2714 signed
{esp_path}/EFI/Linux/test.efi
{"Status":>10} \u2717 not signed
{esp_path}/EFI/Linux/test2.efi
{"Status":>10} \u2714 signed
{esp_path}/test3.efi
{"Status":>10} \u2714 signed
        '''.rstrip(),
                         stdout_mock.getvalue().rstrip()
                         )

    @patch('sys.stdout', new_callable=StringIO)
    @patch('secbootctl.features.file.Path.is_dir')
    @patch('secbootctl.features.file.glob')
    def test_list_if_all_it_lists_all_files(self, glob_patch_mock: MagicMock, path_is_dir_patch_mock,
                                            stdout_mock: MagicMock):
        esp_path = Path('/boot/efi')
        self._config_mock.configure_mock(esp_path=esp_path)
        glob_patch_mock.glob.return_value = [
            f'{esp_path}/EFI/Linux/test.efi',
            f'{esp_path}/EFI/Linux/test2.efi',
            f'{esp_path}/EFI/Linux/test4.txt',
            f'{esp_path}/test3.efi'
        ]
        path_is_dir_patch_mock.return_value = False
        self._sb_helper_mock.verify_file.side_effect = [True, False, False, True]

        self._controller.list(True)

        glob_patch_mock.glob.assert_called_once_with(
            str(esp_path / '**' / '*'), recursive=True
        )

        self.assertEqual(f'''{esp_path}/EFI/Linux/test.efi
{"Status":>10} \u2714 signed
{esp_path}/EFI/Linux/test2.efi
{"Status":>10} \u2717 not signed
{esp_path}/EFI/Linux/test4.txt
{"Status":>10} \u2717 not signed
{esp_path}/test3.efi
{"Status":>10} \u2714 signed
        '''.rstrip(),
                         stdout_mock.getvalue().rstrip()
                         )

    def test_sign_it_signs_given_file(self):
        file_path: Path = Path('/tmp/file.efi')
        self._sb_helper_mock.sign_file.return_value = True

        self._controller.sign(str(file_path))

        self._sb_helper_mock.sign_file.assert_called_once_with(
            file_path, False
        )
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'signing: {file_path}', CliPrintHelper.Status.PENDING),
            call(f'signed: {file_path}', CliPrintHelper.Status.SUCCESS)
        ])

    def test_sign_if_signing_fails_it_raises_an_error(self):
        file_path: Path = Path('/tmp/file.efi')
        self._sb_helper_mock.sign_file.return_value = False

        with self.assertRaises(AppError) as context_manager:
            self._controller.sign(str(file_path))

        error: AppError = context_manager.exception
        self._cli_print_helper_mock.print_status.assert_called_once_with(
            f'signing: {file_path}', CliPrintHelper.Status.PENDING
        )
        self._sb_helper_mock.sign_file.assert_called_once_with(
            file_path, False
        )
        self.assertEqual(
            error.message,
            f'failed to sign: {file_path}'
        )
        self.assertEqual(
            error.code,
            1
        )

    def test_verify_it_verifies_signature_of_given_file(self):
        file_path: Path = Path('/tmp/file.efi')
        self._sb_helper_mock.verify_file.return_value = True

        self._controller.verify(str(file_path))

        self._sb_helper_mock.verify_file.assert_called_once_with(
            file_path
        )
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'verifying signature: {file_path}', CliPrintHelper.Status.PENDING),
            call(f'valid signature: {file_path}', CliPrintHelper.Status.SUCCESS)
        ])

    def test_verify_if_signature_verification_fails_it_prints_invalid_signature_message(self):
        file_path: Path = Path('/tmp/file.efi')
        self._sb_helper_mock.verify_file.return_value = False

        self._controller.verify(str(file_path))

        self._sb_helper_mock.verify_file.assert_called_once_with(
            file_path
        )
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'verifying signature: {file_path}', CliPrintHelper.Status.PENDING),
            call(f'invalid signature: {file_path}', CliPrintHelper.Status.ERROR)
        ])


if __name__ == '__main__':
    unittest.main()
