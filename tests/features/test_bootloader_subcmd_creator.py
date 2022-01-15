import unittest

from tests import unittest_helper


class TestBootloaderSubcmdCreatorController(unittest_helper.SubCmdCreatorTestCase):
    FEATURE_NAME: str = 'bootloader'
    SUBCOMMAND_DATA: list = [
        {'name': 'bootloader:install', 'help_message': 'install bootloader (systemd-boot)'},
        {'name': 'bootloader:update', 'help_message': 'update bootloader (systemd-boot)'},
        {'name': 'bootloader:remove', 'help_message': 'remove bootloader (systemd-boot)'},
        {'name': 'bootloader:status', 'help_message': 'show bootloader status (systemd-boot)'},
        {'name': 'bootloader:update-menu', 'help_message': 'update bootloader menu'}
    ]


if __name__ == '__main__':
    unittest.main()
