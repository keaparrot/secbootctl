import unittest

from tests import unittest_helper


class TestConfigSubcmdCreatorController(unittest_helper.SubCmdCreatorTestCase):
    FEATURE_NAME: str = 'config'
    SUBCOMMAND_DATA: list = [
        {'name': 'config:list', 'help_message': 'list current config'}
    ]


if __name__ == '__main__':
    unittest.main()
