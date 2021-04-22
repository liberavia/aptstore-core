# -*- coding: utf-8 -*-
import os
import subprocess
import apt
from . import ACTION_ADD
from . import PLATFORM_STEAM
from .platform import Platform


class Steam(Platform):
    """
    Steam platform
    """

    def __init__(self):
        super().__init__()
        self.data = {
            'paths': {
                'steam': os.path.expanduser('~') + '/.aptstore/steam/',
                'progress': os.path.expanduser('~') + '/.aptstore/progress/',
                'binaries': os.path.expanduser('~') + '/.aptstore/bin/',
            },
            'binaries': {
                'steamcmd': os.path.expanduser('~') + '/.aptstore/bin/steamcmd.sh',
            },
            'downloads': {
                'steamcmd': {
                    'source': 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz',
                    'target': os.path.expanduser('~') + '/.aptstore/bin/steamcmd.tar.gz',
                    'type': 'tarfile',
                    'validate': {
                        'steamcmd': os.path.expanduser('~') + '/.aptstore/bin/steamcmd.sh',
                        'linux32': os.path.expanduser('~') + '/.aptstore/bin/linux32',
                    }
                },
            },
        }
        self.initialize_platform()

    def install(self, **kwargs):
        """
        Validate params and install app with given id
        :param kwargs:
        :return:
        """
        try:
            self.platform_initialized()
            expected_params = self.get_install_params()
            self.validate_params(kwargs.keys(), expected_params)
        except ValueError:
            return

        login = kwargs.get('login')
        password = kwargs.get('password')
        appid = kwargs.get('ident')
        self.install_steam_app(appid, login, password)

    def remove(self, **kwargs):
        """
        Validate params and remove app with given id
        :param kwargs:
        :return:
        """
        try:
            self.platform_initialized()
            expected_params = self.get_install_params()
            self.validate_params(kwargs.keys(), expected_params)
        except ValueError:
            return

        login = kwargs.get('login')
        password = kwargs.get('password')
        appid = kwargs.get('ident')
        self.remove_steam_app(appid, login, password)

    def install_steam_app(self, appid, login, password):
        """
        Performing installation of a steam app

        :param appid:
        :param login:
        :param password:
        :return:
        """
        steamcmd = self.data['binaries']['steamcmd']
        progress_path = self.data['paths']['progress']
        message_output_file = self.get_message_filename(userident=login, appident=appid)
        message_file_path = os.path.join(progress_path, message_output_file)

        command_elements = [
            'unbuffer',
            steamcmd,
            '+login',
            login,
            password,
            '+app_update',
            appid,
            'validate',
            '+quit',
            '>>',
            message_file_path
        ]

        start_command = ' '.join(command_elements)
        subprocess.Popen(start_command, shell=True, close_fds=True)
        print(
            "Installing app via {platform}. Follow progress at {logfile}".
                format(
                platform=PLATFORM_STEAM,
                logfile=message_file_path)
        )

    def remove_steam_app(self, appid, login, password):
        """
        Performing removal of a steam app

        :param appid:
        :param login:
        :param password:
        :return:
        """
        steamcmd = self.data['binaries']['steamcmd']
        progress_path = self.data['paths']['progress']
        message_output_file = self.get_message_filename(userident=login, appident=appid)
        message_file_path = os.path.join(progress_path, message_output_file)

        command_elements = [
            'unbuffer',
            steamcmd,
            '+login',
            login,
            password,
            '+app_uninstall -complete',
            appid,
            '+quit',
            '>>',
            message_file_path
        ]

        remove_command = ' '.join(command_elements)
        subprocess.Popen(remove_command, shell=True, close_fds=True)
        print(
            "Removing app via {platform}. Follow progress at {logfile}".
                format(
                platform=PLATFORM_STEAM,
                logfile=message_file_path)
        )

    def get_install_params(self):
        """
        Returns list of expected params for a proper installation
        :return: list
        """
        params = [
            'platform',
            'action',
            'ident',
            'login',
            'password',
        ]

        return params

    def get_platform_dependencies(self):
        """
        Returns list needed debian packages that need to be installed
        :return: list
        """
        params = [
            'expect',
            'steam:i386',
        ]

        return params

    def initialize_platform(self):
        self.create_paths()
        self.perform_downloads()

    def platform_initialized(self):
        """
        Check if all needed elements for platform are available
        :return:
        """
        # steamcmd downloaded
        steamcmd = self.data['binaries']['steamcmd']
        steamcmd_exists = os.path.isfile(steamcmd)
        if not steamcmd_exists:
            raise ValueError("steamcmd not available!")

        # needed system packages installed
        try:
            self.check_system_packages()
        except ValueError:
            raise ValueError("Not all packages available")

        return True

    def activate_platform(self):
        """
        Install needed system dependencies
        :return:
        """

        if os.getuid() != 0:
            raise ValueError(
                "Activating a platform needs root rights." 
                "Please use 'sudo aptstore steam {action}' instead".format(action=ACTION_ADD)
            )

        cache = apt.cache.Cache()
        cache.update()
        cache.open()

        packages = self.get_platform_dependencies()
        for pkg_name in packages:
            pkg = cache[pkg_name]
            if not pkg.is_installed:
                pkg.mark_install()
        cache.commit()
