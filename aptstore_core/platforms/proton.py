# -*- coding: utf-8 -*-

import os
import time
import subprocess
from . import PLATFORM_PROTON
from .steam import Steam
from ..reporting import REPORT_TYPE_PROGRESS


class Proton(Steam):
    """
    Steam platform via proton
    """

    def __init__(self, **kwargs):
        super(Proton, self).__init__(**kwargs)
        self.platform_name = PLATFORM_PROTON

    def install_steam_app(self):
        """
        Performing installation of a steam proton app
        :return:
        """
        steamcmd = self.data['binaries']['steamcmd']
        progress_path = self.data['paths']['progress']
        progress_file = self.get_progress_filename(userident=self.login, appident=self.ident)
        progress_file_path = os.path.join(progress_path, progress_file)

        if os.path.isfile(progress_file_path):
            raise FileExistsError("Process already running. Abort.")

        command_elements = [
            'unbuffer',
            steamcmd,
            '+@sSteamCmdForcePlatformType windows',
            '+login',
            self.login,
            self.password,
            '+app_update',
            self.ident,
            'validate',
            '+quit',
            '>>',
            progress_file_path
        ]

        start_command = ' '.join(command_elements)
        process = subprocess.Popen(start_command, shell=True, close_fds=True)
        print(
            "Install app via {platform}. Follow progress at {logfile}".format(
                platform=PLATFORM_PROTON,
                logfile=progress_file_path)
        )

        while process.poll() is None:
            time.sleep(1)
            self.reporter.create_report(REPORT_TYPE_PROGRESS)
        print("Finished")
        try:
            os.remove(progress_file_path)
        except FileNotFoundError:
            pass
        self.reporter.delete_report()
        self.update_installed_apps()

    def activate_platform(self):
        """
        Perform anything needed
        :return:
        """
        print(
            "Activating proton is done by activating "
            "steam platform by typing: sudo aptstore-core steam activate"
        )
