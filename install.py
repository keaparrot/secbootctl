#!/usr/bin/env python3
#
# secbootctl - Secure Boot Helper
#
# @license https://github.com/keaparrot/secbootctl/blob/master/LICENSE.md

from __future__ import annotations

import os
import shutil
import zipapp
from pathlib import Path

if __name__ == '__main__':
    ETC_APP_PATH: Path = Path('/etc/secbootctl')
    ETC_APP_CONFIG_FILE_PATH: Path = ETC_APP_PATH / 'secbootctl.conf'
    USR_FILE_PATH: Path = Path('/usr/local/bin/secbootctl')

    try:
        if os.getuid() != 0:
            raise RuntimeError('root permissions required')

        # zip project directory content and copy it as executable to /usr/local/bin/secbootctl
        # (actually it would be enough to zip only '__main.py__' and 'secbootctl' subdirectory)
        zipapp.create_archive('.', USR_FILE_PATH, '/usr/bin/env python3')
        shutil.chown(USR_FILE_PATH, 'root', 'root')
        USR_FILE_PATH.chmod(0o755)

        # create /etc/secbootctl directory structure and just because of a bit of paranoia sets permissions explicitly
        os.mkdir(ETC_APP_PATH, 0o755)
        os.mkdir(ETC_APP_PATH / 'keys', 0o700)
        shutil.copyfile('secbootctl.conf', ETC_APP_CONFIG_FILE_PATH)

        shutil.chown(ETC_APP_CONFIG_FILE_PATH, 'root', 'root')
        ETC_APP_CONFIG_FILE_PATH.chmod(0o644)

        shutil.copytree('hooks', ETC_APP_PATH / 'hooks')
        for directory_path, directory_names, file_names in os.walk(ETC_APP_PATH / 'hooks'):
            directory_path: Path = Path(directory_path)
            shutil.chown(directory_path, 'root', 'root')
            directory_path.chmod(0o755)

            for file_name in file_names:
                file_path: Path = directory_path / file_name
                shutil.chown(file_path, 'root', 'root')
                file_path.chmod(0o600)
    except Exception as error:
        print(f'an error occurred: {error}')
