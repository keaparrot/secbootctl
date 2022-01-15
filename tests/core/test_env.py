import unittest
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from secbootctl.env import Env


class TestEnv(unittest.TestCase):
    @patch('secbootctl.env.Path')
    def test_load_it_sets_machine_id(self, path_patch_mock: MagicMock):
        path_mock = Mock()
        path_patch_mock.return_value = path_mock
        machine_id = '1234-5678\n'
        path_mock.read_text.return_value = machine_id

        Env.load()

        path_patch_mock.assert_called_once_with(
            '/etc/machine-id'
        )
        self.assertEqual(
            machine_id.rstrip(),
            Env.MACHINE_ID
        )


if __name__ == '__main__':
    unittest.main()
