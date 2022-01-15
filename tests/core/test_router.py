import unittest

from secbootctl.core import Router


class TestRouter(unittest.TestCase):
    def setUp(self) -> None:
        self._router: Router = Router()

    def test_match_it_returns_resolved_route_data(self):
        cli_request_data: dict = {'command_name': 'kernel:install', 'kernel_name': 'linux-custom'}

        self.assertDictEqual(
            {
                'module_name': 'secbootctl.features.kernel',
                'controller_name': 'KernelController',
                'action_name': 'install',
                'params': {'kernel_name': 'linux-custom'}
            },
            self._router.match(cli_request_data)
        )


if __name__ == '__main__':
    unittest.main()
