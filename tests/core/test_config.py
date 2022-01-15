import unittest
from pathlib import Path
from unittest.mock import MagicMock

from secbootctl.core import Config, AppError


class TestConfig(unittest.TestCase):
    def setUp(self) -> None:
        self._config_parser_mock: MagicMock = MagicMock()
        self._config: Config = Config(self._config_parser_mock)

        self._config_data: dict = {
            'boot_path': '/boot',
            'esp_path': '/efi',
            'sb_keys_path': '/keys',
            'default_kernel': 'linux',
            'include_microcode': 'yes',
            'kernel_image_name_prefix': 'vmlinuz123',
            'initramfs_image_name_template': 'initramfs123',
            'microcode_image_name': 'micorocode123',
            'bootloader_menu_editor': 'yes',
            'bootloader_menu_timeout': 5,
            'package_manager': 'pacman123'
        }
        self._config._config_data = self._config_data

    def test_init_it_assigns_given_dependencies(self):
        self.assertIs(
            self._config_parser_mock,
            self._config._config_parser
        )

    def test_load_if_config_file_is_readable_it_loads_config_from_config_file(self):
        config_file_path: Path = Path('/tmp/conf')
        self._config_parser_mock.read.return_value = [config_file_path]
        config_data: dict = {'c1': 'cv1', 'c2': 'cv2'}
        self._config_parser_mock.__getitem__.return_value = config_data
        self._config._config_data = {}

        self._config.load(config_file_path)

        self._config_parser_mock.read.assert_called_once_with(
            config_file_path
        )
        self.assertDictEqual(
            config_data,
            self._config._config_data
        )

    def test_load_if_config_file_is_not_readable_it_raises_an_error(self):
        config_file_path: Path = Path('/tmp/conf')
        self._config_parser_mock.read.return_value = []

        with self.assertRaises(AppError) as context_manager:
            self._config.load(config_file_path)

        self._config_parser_mock.read.assert_called_once_with(
            config_file_path
        )
        error: AppError = context_manager.exception
        self.assertEqual(
            error.message,
            f'could not read configuration file "{config_file_path}"'
        )
        self.assertEqual(
            error.code,
            1
        )

    def test_config_data_it_returns_config_data(self):
        self.assertDictEqual(
            self._config_data,
            self._config.config_data
        )

    def test_boot_path_it_returns_boot_path(self):
        self.assertEqual(
            Path(self._config_data['boot_path']),
            self._config.boot_path
        )

    def test_esp_path_it_returns_esp_path(self):
        self.assertEqual(
            Path(self._config_data['esp_path']),
            self._config.esp_path
        )

    def test_sb_keys_path_it_returns_sb_keys_path(self):
        self.assertEqual(
            Path(self._config_data['sb_keys_path']),
            self._config.sb_keys_path
        )

    def test_default_kernel_it_returns_default_kernel_name(self):
        self.assertEqual(
            self._config_data['default_kernel'],
            self._config.default_kernel_name
        )

    def test_include_microcode_if_yes_it_returns_true(self):
        self.assertTrue(
            self._config.include_microcode
        )

    def test_include_microcode_if_no_it_returns_false(self):
        self._config._config_data['include_microcode'] = 'no'

        self.assertFalse(
            self._config.include_microcode
        )

    def test_kernel_image_name_prefix_it_returns_kernel_image_name_prefix(self):
        self.assertEqual(
            self._config_data['kernel_image_name_prefix'],
            self._config.kernel_image_name_prefix
        )

    def test_initramfs_image_name_template_it_returns_initramfs_image_name_template(self):
        self.assertEqual(
            self._config_data['initramfs_image_name_template'],
            self._config.initramfs_image_name_template
        )

    def test_microcode_image_name_it_returns_microcode_image_name(self):
        self.assertEqual(
            self._config_data['microcode_image_name'],
            self._config.microcode_image_name
        )

    def test_bootloader_menu_editor_it_returns_bootloader_menu_editor(self):
        self.assertEqual(
            self._config_data['bootloader_menu_editor'],
            self._config.bootloader_menu_editor
        )

    def test_bootloader_menu_timeout_it_returns_bootloader_menu_timeout(self):
        self.assertEqual(
            self._config_data['bootloader_menu_timeout'],
            self._config.bootloader_menu_timeout
        )

    def test_package_manager_it_returns_package_manager_name(self):
        self.assertEqual(
            self._config_data['package_manager'],
            self._config.package_manager_name
        )


if __name__ == '__main__':
    unittest.main()
