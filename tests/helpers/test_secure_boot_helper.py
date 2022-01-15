import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from secbootctl.env import Env
from secbootctl.helpers.secureboot import SecureBootHelper


class TestSecureBootHelper(unittest.TestCase):
    def setUp(self) -> None:
        self._process_result_mock: Mock = Mock()
        self._file_path: Path = Path('/tmp/file.efi')
        self._key_path: Path = Path('/tmp/keys')
        self._db_key_file_path = self._key_path / (Env.SB_KEY_NAME_DB + '.key')
        self._db_cert_file_path = self._key_path / (Env.SB_KEY_NAME_DB + '.crt')
        self._sb_helper: SecureBootHelper = SecureBootHelper(self._key_path)

    def test_init_it_assigns_key_file_paths(self):
        self.assertEqual(
            self._db_key_file_path,
            self._sb_helper._db_key_file_path
        )
        self.assertEqual(
            self._db_cert_file_path,
            self._sb_helper._db_cert_file_path
        )

    @patch('secbootctl.helpers.secureboot.subprocess')
    def test_sign_file_if_signing_is_successful_it_returns_true(self, subprocess_patch_mock: MagicMock):
        subprocess_patch_mock.run.return_value = self._process_result_mock
        self._process_result_mock.configure_mock(returncode=0)

        self.assertTrue(
            self._sb_helper.sign_file(self._file_path)
        )

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'sbsign',
                f'--key={self._db_key_file_path}',
                f'--cert={self._db_cert_file_path}',
                f'--output={self._file_path}',
                self._file_path
            ], capture_output=True
        )

    @patch('secbootctl.helpers.secureboot.subprocess')
    def test_sign_file_if_signing_fails_it_returns_false(self, subprocess_patch_mock: MagicMock):
        subprocess_patch_mock.run.return_value = self._process_result_mock
        self._process_result_mock.configure_mock(returncode=1)

        self.assertFalse(
            self._sb_helper.sign_file(self._file_path)
        )

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'sbsign',
                f'--key={self._db_key_file_path}',
                f'--cert={self._db_cert_file_path}',
                f'--output={self._file_path}',
                self._file_path
            ], capture_output=True
        )

    @patch('secbootctl.helpers.secureboot.subprocess')
    def test_sign_file_if_verification_is_successful_it_returns_true(self, subprocess_patch_mock: MagicMock):
        subprocess_patch_mock.run.return_value = self._process_result_mock
        self._process_result_mock.configure_mock(returncode=0)

        self.assertTrue(
            self._sb_helper.verify_file(self._file_path)
        )

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'sbverify',
                f'--cert={self._db_cert_file_path}',
                self._file_path
            ], capture_output=True
        )

    @patch('secbootctl.helpers.secureboot.subprocess')
    def test_sign_file_if_verifications_fails_it_returns_false(self, subprocess_patch_mock: MagicMock):
        subprocess_patch_mock.run.return_value = self._process_result_mock
        self._process_result_mock.configure_mock(returncode=1)

        self.assertFalse(
            self._sb_helper.verify_file(self._file_path)
        )

        subprocess_patch_mock.run.assert_called_once_with(
            [
                'sbverify',
                f'--cert={self._db_cert_file_path}',
                self._file_path
            ], capture_output=True
        )


if __name__ == '__main__':
    unittest.main()
