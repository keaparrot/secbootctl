import unittest
from io import StringIO
from unittest.mock import MagicMock
from unittest.mock import patch

from secbootctl.env import Env
from tests import unittest_helper


class TestConfigController(unittest_helper.ControllerTestCase):
    FEATURE_NAME: str = 'config'

    @patch('sys.stdout', new_callable=StringIO)
    def test_list_it_lists_configuration(self, stdout_mock: MagicMock):
        config_data: dict = {'boot_path': '/boot', 'esp_path': '/boot/efi'}
        self._config_mock.configure_mock(config_data=config_data)

        self._controller.list()

        self.assertEqual(f'''{"Config-Name":35} Config-Value\n{"---":35} ---
{"boot_path":35} /boot
{"esp_path":35} /boot/efi

Configuration file: "{Env.APP_CONFIG_FILE_PATH}"
            '''.rstrip(),
            stdout_mock.getvalue().rstrip()
        )


if __name__ == '__main__':
    unittest.main()
