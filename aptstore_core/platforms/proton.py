# -*- coding: utf-8 -*-
import apt
import os
import subprocess
from . import PLATFORM_PROTON
from .steam import Steam


class Proton(Steam):
    """
    Steam platform via proton
    """

    def __init__(self, action=None):
        super(Proton, self).__init__(action)
        self.platform_name = PLATFORM_PROTON

    def install_steam_app(self, login, password):
        """
        Performing installation of a steam proton app

        :param appid:
        :param login:
        :param password:
        :return:
        """
        steamcmd = self.data['binaries']['steamcmd']
        progress_path = self.data['paths']['progress']
        progress_file = self.get_progress_filename(userident=login, appident=self.ident)
        progress_file_path = os.path.join(progress_path, progress_file)

        if os.path.isfile(progress_file_path):
            raise FileExistsError("Process already running. Abort.")

        command_elements = [
            'unbuffer',
            steamcmd,
            '+@sSteamCmdForcePlatformType windows',
            '+login',
            login,
            password,
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
            "Install app via {platform}. Follow progress at {logfile}".
                format(
                platform=PLATFORM_PROTON,
                logfile=progress_file_path)
        )
        process.communicate()
        print("Finished")
        os.remove(progress_file_path)

    def remove_steam_app(self, login, password):
        """
        Performing removal of a steam proton app

        :param appid:
        :param login:
        :param password:
        :return:
        """
        steamcmd = self.data['binaries']['steamcmd']
        progress_path = self.data['paths']['progress']
        progress_file = self.get_progress_filename(userident=login, appident=self.ident)
        progress_file_path = os.path.join(progress_path, progress_file)

        if os.path.isfile(progress_file_path):
            raise FileExistsError("Process already running. Abort.")

        command_elements = [
            'unbuffer',
            steamcmd,
            '+login',
            login,
            password,
            '+app_uninstall',
            self.ident,
            '+quit',
            '>>',
            progress_file_path
        ]

        start_command = ' '.join(command_elements)
        process = subprocess.Popen(start_command, shell=True, close_fds=True)
        print(
            "Remove app via {platform}. Follow progress at {logfile}".
                format(
                platform=PLATFORM_PROTON,
                logfile=progress_file_path)
        )
        process.communicate()
        print("Finished")
        os.remove(progress_file_path)

    def activate_platform(self):
        """
        Perform anything needed
        :return:
        """
        print(
            "Activating proton is done by activating "
            "steam platform by typing: sudo aptstore-core steam activate"
        )
