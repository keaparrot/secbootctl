import unittest

from tests import unittest_helper


class TestBootloaderSubcmdCreatorController(unittest_helper.SubCmdCreatorTestCase):
    FEATURE_NAME: str = 'file'
    SUBCOMMAND_DATA: list = [
        {'name': 'file:list', 'help_message': 'list files on ESP with signing status'},
        {'name': 'file:sign', 'help_message': 'sign given file'},
        {'name': 'file:verify', 'help_message': 'verify signature of given file'},
    ]


if __name__ == '__main__':
    unittest.main()
