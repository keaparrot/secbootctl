import unittest
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from secbootctl.core import App
from secbootctl.env import Env


class TestApp(unittest.TestCase):
    def setUp(self) -> None:
        self._config_mock: Mock = Mock()
        self._cli_cmd_manager: Mock = Mock()
        self._router_mock: Mock = Mock()
        self._dispatcher_mock: Mock = Mock()
        self._app: App = App(
            self._config_mock, self._cli_cmd_manager, self._router_mock, self._dispatcher_mock
        )

    def test_init_it_assigns_given_dependencies(self):
        self.assertIs(
            self._config_mock,
            self._app._config
        )
        self.assertIs(
            self._cli_cmd_manager,
            self._app._cli_cmd_manager
        )
        self.assertIs(
            self._router_mock,
            self._app._router
        )
        self.assertIs(
            self._dispatcher_mock,
            self._app._dispatcher
        )

    @patch.object(Env, 'load')
    def test_run_it_loads_environment(self, env_load_method_mock: MagicMock):
        self._app.run()

        env_load_method_mock.assert_called_once()

    def test_run_it_loads_config(self):
        self._app.run()

        self._config_mock.load.assert_called_once_with(
            Env.APP_CONFIG_FILE_PATH
        )

    def test_run_it_initializes_cli_commands(self):
        esp_path: Path = Path('/tmp/efi')
        self._config_mock.configure_mock(esp_path=esp_path)

        self._app.run()

        self._cli_cmd_manager.init_commands.assert_called_once_with(
            esp_path
        )

    def test_run_it_invokes_dispatching(self):
        cli_request_data: dict = {'command_name': 'kernel:install'}
        route_data: dict = {
            'module_name': 'secbootctl.features.kernel',
            'controller_name': 'KernelController',
            'action_name': 'install'
        }
        self._cli_cmd_manager.parse_request.return_value = cli_request_data
        self._router_mock.match.return_value = route_data

        self._app.run()

        self._router_mock.match.assert_called_once_with(
            cli_request_data
        )
        self._dispatcher_mock.dispatch.assert_called_once_with(
            route_data
        )


if __name__ == '__main__':
    unittest.main()
