# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
from pathlib import Path

import secbootctl.core
from secbootctl.env import Env


class KernelOsHelper:
    def __init__(self, config: secbootctl.core.Config):
        self._config: secbootctl.core.Config = config

    def check_requirements(self) -> None:
        """Checks that script is called with root permissions and that OS is booted via UEFI."""
        if os.getuid() != 0:
            raise secbootctl.core.AppError('root permissions required')
        elif not Path(Env.EFI_BOOT_MODE_CHECK_PATH).is_dir():
            raise secbootctl.core.AppError('UEFI boot mode required')

    def build_unified_kernel_image(self, kernel_name: str, unified_kernel_image_path: Path) -> None:
        """Builds unified kernel image for given kernel name and copies it to "<efi_path>/EFI/Linux".

        Unified kernel image contains kernel cmdline, os-release, kernel, initramfs and if configured
        (see configuration file) microcode image.

        see https://wiki.archlinux.org/title/systemd-boot#Preparing_a_unified_kernel_image
        """
        boot_path: Path = self._config.boot_path
        kernel_image_path: Path = boot_path / (self._config.kernel_image_name_prefix + '-' + kernel_name)
        initramfs_image_path: Path = boot_path / self._config.initramfs_image_name_template.replace(
            '__kernel-name__', kernel_name)
        microcode_image_path: Path = boot_path / self._config.microcode_image_name
        microcode_initramfs_unified_image_path: Path = boot_path / 'tmp-microcode-initramfs-unified.img'
        objcopy_initrd_image_path: Path = initramfs_image_path
        kernel_cmdline_file_path: Path = Env.KERNEL_CMDLINE_ETC_FILE_PATH

        if not kernel_cmdline_file_path.is_file():
            kernel_cmdline_file_path = Env.KERNEL_CMDLINE_PROC_FILE_PATH

        if self._config.include_microcode:
            with open(microcode_initramfs_unified_image_path, 'wb') as combined_image:
                with open(microcode_image_path, 'rb') as microcode_image:
                    shutil.copyfileobj(microcode_image, combined_image)

                with open(initramfs_image_path, 'rb') as initramfs_image:
                    shutil.copyfileobj(initramfs_image, combined_image)

            objcopy_initrd_image_path = microcode_initramfs_unified_image_path

        process_result = subprocess.run([
            'objcopy',
            f'--add-section=.osrel={Env.OS_RELEASE_FILE_PATH}',
            '--change-section-vma=.osrel=0x20000',
            f'--add-section=.cmdline={kernel_cmdline_file_path}',
            '--change-section-vma=.cmdline=0x30000',
            f'--add-section=.linux={kernel_image_path}',
            '--change-section-vma=.linux=0x2000000',
            f'--add-section=.initrd={objcopy_initrd_image_path}',
            '--change-section-vma=.initrd=0x3000000',
            Env.BOOTLOADER_SYSTEMD_BOOT_STUB_FILE_PATH,
            unified_kernel_image_path
        ], capture_output=True)

        microcode_initramfs_unified_image_path.unlink(missing_ok=True)

        if process_result.returncode != 0:
            raise secbootctl.core.AppError(f'building unified kernel image "{unified_kernel_image_path}" failed')

    def get_default_kernel_name(self) -> str:
        """Returns default configured kernel name.

        If kernel name is "latest" then latest kernel will be determined by sorting "<boot_path>/vmlinuz-*"
        descending and taking the first result.
        """
        default_kernel_name: str = self._config.default_kernel_name

        if default_kernel_name == 'latest':
            boot_path: Path = self._config.boot_path
            kernel_image_paths: list = glob.glob(str(boot_path / (self._config.kernel_image_name_prefix + '-*')))
            kernel_image_paths.sort(reverse=True)

            default_kernel_name = kernel_image_paths[0].replace(str(boot_path), '').split('-', 1)[1]

        return default_kernel_name

    def get_unified_kernel_image_path(self, kernel_name: str) -> Path:
        """Returns unified kernel image path for given kernel name.

        Format of unified image name: <machine_id>-<kernel_name>-{os_id}.efi

        see https://systemd.io/BOOT_LOADER_SPECIFICATION/
        """
        return self._config.esp_path / Env.UNIFIED_IMAGE_SUBPATH / (
            Env.MACHINE_ID + '-' + kernel_name + '-' + self.get_os_id() + '.efi')

    def get_kernel_version(self, kernel_name) -> str:
        """Returns kernel version for given kernel name.

        On Debian-like systems kernel name is usually equal to kernel version (e.g. 5.4.0-91-generic).
        """
        kernel_version: str = kernel_name

        if self._config.package_manager_name == 'pacman':
            process_result = subprocess.run(['pacman', '-Q', kernel_name], capture_output=True)

            if process_result.returncode != 0:
                raise secbootctl.core.AppError(
                    f'could not resolve kernel version with pacman for kernel name "{kernel_name}"'
                )

            kernel_version = process_result.stdout.decode().split(' ', 1)[1].rstrip()

        return kernel_version

    def get_os_id(self) -> str:
        """Returns ID-value found in '/etc/os-release'."""
        return self._get_os_release_value('ID')

    def get_os_pretty_name(self) -> str:
        """Returns PRETTY_NAME-value found in '/etc/os-release'."""
        return self._get_os_release_value('PRETTY_NAME')

    def _get_os_release_value(self, key: str) -> str:
        """Returns value found for given key in '/etc/os-release'."""
        os_value: str = ''

        with open(Env.OS_RELEASE_FILE_PATH, 'rt') as file:
            for line in file:
                if re.match(key + '=', line):
                    os_value = line.split('=', 1)[1].rstrip()

                    break

        return os_value
