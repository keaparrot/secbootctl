# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Optional

from secbootctl.core import AppController, BaseSubcmdCreator
from secbootctl.env import Env
from secbootctl.helpers.cli import CliPrintHelper


class KernelController(AppController):
    def install(self, kernel_name: Optional[str] = None) -> None:
        """Installs given kernel or default kernel (see configuration file) when no argument given.

        Install steps:
            1. Builds unified kernel image that consists of kernel, initramfs and microcode image.
            2. Signs unified kernel image.
            3. Verifies signature of unified kernel image.
        """
        if kernel_name is None:
            kernel_name = self._kernel_os_helper.get_default_kernel_name()

        unified_kernel_image_path: Path = self._kernel_os_helper.get_unified_kernel_image_path(kernel_name)

        self._build_unified_kernel_image(kernel_name, unified_kernel_image_path)
        self._sign_file(unified_kernel_image_path)
        self._verify_file(unified_kernel_image_path)

    def remove(self, kernel_name: Optional[str] = None) -> None:
        """Removes given kernel or default kernel (see configuration file) when no argument given."""
        if kernel_name is None:
            kernel_name = self._kernel_os_helper.get_default_kernel_name()

        unified_kernel_image_path: Path = self._kernel_os_helper.get_unified_kernel_image_path(kernel_name)

        self._print_status(f'removing unified kernel image: {unified_kernel_image_path}')

        unified_kernel_image_path.unlink(missing_ok=True)

        self._print_status(f'removed unified kernel image: {unified_kernel_image_path}', CliPrintHelper.Status.SUCCESS)

    def _build_unified_kernel_image(self, kernel_name: str, unified_kernel_image_path: Path) -> None:
        self._print_status(f'building unified kernel image: {unified_kernel_image_path}')

        self._kernel_os_helper.build_unified_kernel_image(kernel_name, unified_kernel_image_path)

        self._print_status(f'built unified kernel image: {unified_kernel_image_path}', CliPrintHelper.Status.SUCCESS)


class KernelSubcmdCreator(BaseSubcmdCreator):
    def create(self, cli_subparsers):
        ki_cli_subparser = self._add(cli_subparsers, 'kernel:install', 'install given or default kernel',
                                     textwrap.dedent(f'''
            Install the given or default configured kernel as signed unified kernel image.

            The following steps will be performed:
                - building unified kernel image for given or default configured kernel
                    - contains kernel cmdline, os-release, kernel, initramfs and optionally microcode image
                    - scheme of file name: "|Machine-ID|-|Kernel-Version|-|OS-ID|.efi"
                    - will be moved to "{self._esp_path}/{Env.UNIFIED_IMAGE_SUBPATH}"
                - signing unified kernel image
                - verifying signature of unified kernel image
        '''))
        ki_cli_subparser.add_argument('kernel_name', nargs='?', help='e.g. "linux-lts", "5.4.0-91-generic", etc.')
        kr_cli_subparser = self._add(cli_subparsers, 'kernel:remove', 'remove given or default kernel',
                                     textwrap.dedent('''
            Remove the given or default configured kernel.

            The following step will be performed:
                - removing unified kernel image for given or default configured kernel
        '''))
        kr_cli_subparser.add_argument('kernel_name', nargs='?', help='e.g. "linux-lts", "5.4.0-91-generic", etc.')
