import unittest
from io import StringIO
from unittest.mock import MagicMock
from unittest.mock import patch

from secbootctl.env import Env
from secbootctl.helpers.cli import CliPrintHelper


class TestCliPrintHelper(unittest.TestCase):
    def setUp(self) -> None:
        self._cli_print_helper: CliPrintHelper = CliPrintHelper()

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_status_it_prints_pending_status(self, stdout_mock: MagicMock):
        message: str = 'Message'
        status: CliPrintHelper.Status = CliPrintHelper.Status.PENDING

        self._cli_print_helper.print_status(message, status)

        self.assertEqual(
            f'  {message}',
            stdout_mock.getvalue().rstrip()
        )

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_status_it_prints_success_status(self, stdout_mock: MagicMock):
        message: str = 'Message'
        status: CliPrintHelper.Status = CliPrintHelper.Status.SUCCESS

        self._cli_print_helper.print_status(message, status)

        self.assertEqual(
            f'\u2713 done: {message}',
            stdout_mock.getvalue().rstrip()
        )

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_status_it_prints_error_status(self, stdout_mock: MagicMock):
        message: str = 'Message'
        status: CliPrintHelper.Status = CliPrintHelper.Status.ERROR

        self._cli_print_helper.print_status(message, status)

        self.assertEqual(
            f'\u2717 failed: {message}',
            stdout_mock.getvalue().rstrip()
        )

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_error_it_prints_error_message(self, stdout_mock: MagicMock):
        message: str = 'Error-Message-1'
        code: int = 6

        self._cli_print_helper.print_error(message, code)

        self.assertEqual(
            f'\u2717 ERROR: {message} (Code: {code})\n\nUse "{Env.APP_NAME} --help" for more information.',
            stdout_mock.getvalue().rstrip()
        )


if __name__ == '__main__':
    unittest.main()
