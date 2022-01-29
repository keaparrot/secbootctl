# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

from pathlib import Path


class Env:
    APP_NAME: str = 'secbootctl'
    APP_VERSION: str = '0.1.0'
    APP_TITLE: str = f'{APP_NAME} v{APP_VERSION} - Secure Boot Helper'
    APP_CONFIG_FILE_PATH: Path = Path(f'/etc/{APP_NAME}/{APP_NAME}.conf')
    APP_HOOK_PATH: Path = Path(f'/etc/{APP_NAME}/hooks')
    BOOTLOADER_DEFAULT_BOOT_FILE_SUBPATH: str = 'EFI/BOOT/BOOTX64.EFI'
    BOOTLOADER_SYSTEMD_BOOT_BOOT_FILE_SUBPATH: str = 'EFI/systemd/systemd-bootx64.efi'
    BOOTLOADER_CONFIG_FILE_SUBPATH: str = 'loader/loader.conf'
    BOOTLOADER_DEFAULT_ENTRY_FILE_NAME: str = f'{APP_NAME}-default-linux.conf'
    BOOTLOADER_DEFAULT_ENTRY_FILE_SUBPATH: str = f'loader/entries/{BOOTLOADER_DEFAULT_ENTRY_FILE_NAME}'
    BOOTLOADER_SYSTEMD_BOOT_STUB_FILE_PATH: Path = Path('/usr/lib/systemd/boot/efi/linuxx64.efi.stub')
    EFI_BOOT_MODE_CHECK_PATH: Path = Path('/sys/firmware/efi')
    KERNEL_CMDLINE_ETC_FILE_PATH: Path = Path('/etc/kernel/cmdline')
    KERNEL_CMDLINE_PROC_FILE_PATH: Path = Path('/proc/cmdline')
    MACHINE_ID: str = ''
    OS_RELEASE_FILE_PATH: Path = Path('/etc/os-release')
    SB_KEY_NAME_DB: str = 'db'
    SUPPORTED_PACKAGE_MANAGERS: list = ['pacman', 'apt']
    SUPPORTED_SECURITY_TOKENS: list = ['yubikey']
    UNIFIED_IMAGE_SUBPATH: str = 'EFI/Linux'

    @staticmethod
    def load() -> None:
        Env.MACHINE_ID = Path('/etc/machine-id').read_text().rstrip()
