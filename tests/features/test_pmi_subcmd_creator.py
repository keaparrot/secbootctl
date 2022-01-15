import unittest

from tests import unittest_helper


class TestBootloaderSubcmdCreatorController(unittest_helper.SubCmdCreatorTestCase):
    FEATURE_NAME: str = 'pmi'
    SUBCOMMAND_DATA: list = [
        {'name': 'pmi:install', 'help_message': 'install package manager hook files'},
        {'name': 'pmi:remove', 'help_message': 'remove package manager hook files'},
        {'name': 'pmi:hook-callback', 'help_message': 'package manager hook callback'},
    ]


if __name__ == '__main__':
    unittest.main()
