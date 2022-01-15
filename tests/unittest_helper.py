import importlib
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

from secbootctl.core import AppController, AppError, BaseSubcmdCreator
from secbootctl.helpers.cli import CliPrintHelper, CliCmdUsageHelpFormatter


class ControllerTestCase(unittest.TestCase):
    FEATURE_NAME: str = ''

    @patch('secbootctl.core.SecureBootHelper')
    @patch('secbootctl.core.KernelOsHelper')
    @patch('secbootctl.core.CliPrintHelper')
    def setUp(self, cli_print_helper_patch_mock: MagicMock, kernel_os_helper_patch_mock: MagicMock,
              sb_helper_patch_mock: MagicMock) -> None:
        self._config_mock: Mock = Mock()
        self._dispatcher_mock: Mock = Mock()
        self._cli_print_helper_mock: Mock = Mock()
        cli_print_helper_patch_mock.return_value = self._cli_print_helper_mock
        self._kernel_os_helper_mock: Mock = Mock()
        kernel_os_helper_patch_mock.return_value = self._kernel_os_helper_mock
        self._sb_helper_mock: Mock = Mock()
        sb_helper_patch_mock.return_value = self._sb_helper_mock

        if self.FEATURE_NAME == 'app':
            self._controller = AppController(self._config_mock, self._dispatcher_mock)
        else:
            feature_module: ModuleType = importlib.import_module('secbootctl.features.' + self.FEATURE_NAME)

            self._controller = getattr(
                feature_module,
                self.FEATURE_NAME.capitalize() + 'Controller'
            )(self._config_mock, self._dispatcher_mock)

        self._controller._cli_print_helper = self._cli_print_helper_mock
        self._controller._kernel_os_helper = self._kernel_os_helper_mock
        self._controller._sb_helper = self._sb_helper_mock

    def test_init_it_assigns_given_dependencies(self):
        self.assertIs(
            self._config_mock,
            self._controller._config
        )
        self.assertIs(
            self._dispatcher_mock,
            self._controller._dispatcher
        )

    def test_init_it_checks_requirements(self):
        self._kernel_os_helper_mock.check_requirements.assert_called_once()

    def test_forward_if_no_params_given_it_forwards_given_controller_action_with_no_params(self):
        feature_name: str = 'bootloader'
        action_name: str = 'install'

        self._controller._forward(feature_name, action_name)

        self._dispatcher_mock.dispatch.assert_called_once_with(
            {
                'module_name': 'secbootctl.features.' + feature_name,
                'controller_name': feature_name.capitalize() + 'Controller',
                'action_name': action_name,
                'params': {}
            }
        )

    def test_forward_if_params_given_it_forwards_given_controller_action_with_given_params(self):
        feature_name: str = 'bootloader'
        action_name: str = 'install'
        params: dict = {'p1': 'pv1'}

        self._controller._forward(feature_name, action_name, params)

        self._dispatcher_mock.dispatch.assert_called_once_with(
            {
                'module_name': 'secbootctl.features.' + feature_name,
                'controller_name': feature_name.capitalize() + 'Controller',
                'action_name': action_name,
                'params': params
            }
        )

    def test_print_status_it_prints_status_message(self):
        message: str = 'message'
        status: CliPrintHelper.Status = CliPrintHelper.Status.SUCCESS

        self._controller._print_status(message, status)

        self._cli_print_helper_mock.print_status.assert_called_once_with(
            message, status
        )

    def test_sign_file_it_signs_given_file(self):
        file_path: Path = Path('/tmp/file.efi')
        self._sb_helper_mock.sign_file.return_value = True

        self._controller._sign_file(file_path)

        self._sb_helper_mock.sign_file.assert_called_once_with(
            file_path
        )
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'signing: {file_path}', CliPrintHelper.Status.PENDING),
            call(f'signed: {file_path}', CliPrintHelper.Status.SUCCESS)
        ])

    def test_sign_file_if_signing_fails_it_raises_an_error(self):
        file_path: Path = Path('/tmp/file.efi')
        self._sb_helper_mock.sign_file.return_value = False

        with self.assertRaises(AppError) as context_manager:
            self._controller._sign_file(file_path)

        error: AppError = context_manager.exception
        self._cli_print_helper_mock.print_status.assert_called_once_with(
            f'signing: {file_path}', CliPrintHelper.Status.PENDING
        )
        self._sb_helper_mock.sign_file.assert_called_once_with(
            file_path
        )
        self.assertEqual(
            error.message,
            f'failed to sign: {file_path}'
        )
        self.assertEqual(
            error.code,
            1
        )

    def test_verify_file_it_verifies_signature_of_given_file(self):
        file_path: Path = Path('/tmp/file.efi')
        self._sb_helper_mock.verify_file.return_value = True

        self._controller._verify_file(file_path)

        self._sb_helper_mock.verify_file.assert_called_once_with(
            file_path
        )
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'verifying signature: {file_path}', CliPrintHelper.Status.PENDING),
            call(f'valid signature: {file_path}', CliPrintHelper.Status.SUCCESS)
        ])

    def test_verify_file_if_signature_verification_fails_it_prints_invalid_signature_message(self):
        file_path: Path = Path('/tmp/file.efi')
        self._sb_helper_mock.verify_file.return_value = False

        self._controller._verify_file(file_path)

        self._sb_helper_mock.verify_file.assert_called_once_with(
            file_path
        )
        self._cli_print_helper_mock.print_status.assert_has_calls([
            call(f'verifying signature: {file_path}', CliPrintHelper.Status.PENDING),
            call(f'invalid signature: {file_path}', CliPrintHelper.Status.ERROR)
        ])


class SubCmdCreatorTestCase(unittest.TestCase):
    FEATURE_NAME: str = ''
    SUBCOMMAND_DATA: list = []

    def test_create_it_creates_subcommands(self):
        esp_path: Path = Path('/tmp/efi')
        cli_subparsers_mock: Mock = Mock()
        feature_module: ModuleType = importlib.import_module('secbootctl.features.' + self.FEATURE_NAME)

        creator: BaseSubcmdCreator = getattr(
            feature_module,
            self.FEATURE_NAME.capitalize() + 'SubcmdCreator'
        )(esp_path)

        creator.create(cli_subparsers_mock)

        for subcommand_data in self.SUBCOMMAND_DATA:
            cli_subparsers_mock.add_parser.assert_has_calls([
                call(
                    subcommand_data['name'],
                    help=subcommand_data['help_message'],
                    add_help=False,
                    formatter_class=CliCmdUsageHelpFormatter
                )
            ])


