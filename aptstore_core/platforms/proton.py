# -*- coding: utf-8 -*-
import apt
import os
import subprocess
from . import ACTION_ACTIVATE
from . import PLATFORM_PROTON
from .steam import Steam


class Proton(Steam):
    """
    Steam platform via proton
    """

    def __init__(self):
        super(Proton, self).__init__()
        self.platform_name = PLATFORM_PROTON

    def install_steam_app(self, appid, login, password):
        """
        Performing installation of a steam proton app

        :param appid:
        :param login:
        :param password:
        :return:
        """
        steamcmd = self.data['binaries']['steamcmd']
        progress_path = self.data['paths']['progress']
        progress_file = self.get_progress_filename(userident=login, appident=appid)
        progress_file_path = os.path.join(progress_path, progress_file)

        command_elements = [
            'unbuffer',
            steamcmd,
            '+@sSteamCmdForcePlatformType windows',
            '+login',
            login,
            password,
            '+app_update',
            appid,
            'validate',
            '+quit',
            '>>',
            progress_file_path
        ]

        start_command = ' '.join(command_elements)
        subprocess.Popen(start_command, shell=True, close_fds=True)
        print(
            "Removing app via {platform}. Follow progress at {logfile}".
                format(
                platform=PLATFORM_PROTON,
                logfile=progress_file_path)
        )

    def remove_steam_app(self, appid, login, password):
        """
        Performing removal of a steam proton app

        :param appid:
        :param login:
        :param password:
        :return:
        """
        steamcmd = self.data['binaries']['steamcmd']
        progress_path = self.data['paths']['progress']
        progress_file = self.get_progress_filename(userident=login, appident=appid)
        progress_file_path = os.path.join(progress_path, progress_file)

        command_elements = [
            'unbuffer',
            steamcmd,
            '+login',
            login,
            password,
            '+app_uninstall',
            appid,
            '+quit',
            '>>',
            progress_file_path
        ]

        start_command = ' '.join(command_elements)
        subprocess.Popen(start_command, shell=True, close_fds=True)
        print(
            "Removing app via {platform}. Follow progress at {logfile}".
                format(
                platform=PLATFORM_PROTON,
                logfile=progress_file_path)
        )


