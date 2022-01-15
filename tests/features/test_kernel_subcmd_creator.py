import unittest

from tests import unittest_helper


class TestBootloaderSubcmdCreatorController(unittest_helper.SubCmdCreatorTestCase):
    FEATURE_NAME: str = 'kernel'
    SUBCOMMAND_DATA: list = [
        {'name': 'kernel:install', 'help_message': 'install given or default kernel'},
        {'name': 'kernel:remove', 'help_message': 'remove given or default kernel'},
    ]


if __name__ == '__main__':
    unittest.main()
