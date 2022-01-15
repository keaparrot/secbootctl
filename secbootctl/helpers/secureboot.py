# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

import subprocess
from pathlib import Path

from secbootctl.env import Env


class SecureBootHelper:
    def __init__(self, key_path: Path):
        self._db_key_file_path = key_path / (Env.SB_KEY_NAME_DB + '.key')
        self._db_cert_file_path = key_path / (Env.SB_KEY_NAME_DB + '.crt')

    def sign_file(self, file_path: Path) -> bool:
        """Signs given file.

        see https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot#Signing_EFI_binaries
        """
        process_result = subprocess.run([
            'sbsign',
            f'--key={self._db_key_file_path}',
            f'--cert={self._db_cert_file_path}',
            f'--output={file_path}',
            file_path
        ], capture_output=True)

        return process_result.returncode == 0

    def verify_file(self, file_path: Path) -> bool:
        """Verifies signature of given file.

        see https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot#Signing_EFI_binaries
        """
        process_result = subprocess.run([
            'sbverify',
            f'--cert={self._db_cert_file_path}',
            file_path
        ], capture_output=True)

        return process_result.returncode == 0
