import unittest
from unittest.mock import Mock

from secbootctl.core import Dispatcher


class TestDispatcher(unittest.TestCase):
    def setUp(self) -> None:
        self._controller_factory_mock: Mock = Mock()
        self._dispatcher: Dispatcher = Dispatcher(self._controller_factory_mock)

    def test_init_it_assigns_given_dependencies(self):
        self.assertIs(
            self._controller_factory_mock,
            self._dispatcher._controller_factory
        )

    def test_dispatch_it_dispatches_given_route_data(self):
        controller_mock: Mock = Mock()
        module_name: str = 'secbootctl.features.kernel'
        controller_name: str = 'KernelController'
        params: dict = {'p1': 'pv1'}
        route_data: dict = {
            'module_name': module_name,
            'controller_name': controller_name,
            'action_name': 'install',
            'params': params
        }
        self._controller_factory_mock.create.return_value = controller_mock

        self._dispatcher.dispatch(route_data)

        self._controller_factory_mock.create.assert_called_once_with(
            module_name, controller_name, self._dispatcher
        )
        controller_mock.install.assert_called_once_with(
            **params
        )


if __name__ == '__main__':
    unittest.main()
