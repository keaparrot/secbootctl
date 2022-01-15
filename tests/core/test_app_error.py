import unittest

from secbootctl.core import AppError


class TestAppError(unittest.TestCase):
    def setUp(self) -> None:
        self._message: str = 'Error'
        self._code: int = 5
        self._app_error: AppError = AppError(self._message, self._code)

    def test_init_it_assigns_given_params(self):
        self.assertIs(
            self._message,
            self._app_error._message
        )
        self.assertIs(
            self._code,
            self._app_error._code
        )

    def test_init_it_assigns_default_code_1_if_not_given(self):
        app_error: AppError = AppError(self._message)
        self.assertIs(
            1,
            app_error._code
        )

    def test_message_it_returns_message(self):
        self.assertEqual(
            self._message,
            self._app_error.message
        )

    def test_code_it_returns_code(self):
        self.assertEqual(
            self._code,
            self._app_error.code
        )


if __name__ == '__main__':
    unittest.main()
