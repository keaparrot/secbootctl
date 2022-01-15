import unittest
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

from secbootctl.core import ControllerFactory


class TestControllerFactory(unittest.TestCase):
    def setUp(self) -> None:
        self._config_mock: Mock = Mock()
        self._dispatcher_mock: Mock = Mock()
        self._controller_factory: ControllerFactory = ControllerFactory(self._config_mock)

    def test_init_it_assigns_given_dependencies(self):
        self.assertIs(
            self._config_mock,
            self._controller_factory._config
        )

    @patch('secbootctl.features.kernel.KernelController')
    def test_create_it_returns_instantiated_controller_for_given_name(self, kernel_controller_patch_mock: MagicMock):
        module_name: str = 'secbootctl.features.kernel'
        controller_name: str = 'KernelController'
        kernel_controller_mock: Mock = Mock()
        kernel_controller_patch_mock.return_value = kernel_controller_mock

        self.assertIs(
            kernel_controller_mock,
            self._controller_factory.create(module_name, controller_name, self._dispatcher_mock)
        )
        kernel_controller_patch_mock.assert_called_once_with(
            self._config_mock, self._dispatcher_mock
        )


if __name__ == '__main__':
    unittest.main()
