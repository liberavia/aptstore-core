# -*- coding: utf-8 -*-
import apt
import os
import subprocess
import requests
from . import PLATFORM_STEAM
from .platform import Platform
from . import ACTION_ACTIVATE, ACTION_INSTALL, ACTION_REMOVE


class Steam(Platform):
    """
    Steam platform
    """

    def __init__(self, action=None):
        super(Steam, self).__init__(action)
        self.platform_name = PLATFORM_STEAM
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
            'external_packages': {
                'steamclient': {
                    'source': 'https://cdn.cloudflare.steamstatic.com/client/installer/steam.deb',
                    'target': '/tmp/steam.deb',
                    'type': 'deb'
                }
            },
        }
        self.initialize_platform()

    def install(self, **kwargs):
        """
        Validate params and install app with given id
        :param kwargs:
        :return:
        """
        super(Steam, self).install(**kwargs)
        try:
            self.platform_initialized()
            expected_params = self.get_install_params()
            self.validate_params(kwargs.keys(), expected_params)
        except ValueError:
            return

        login = kwargs.get('login')
        password = kwargs.get('password')
        try:
            self.install_steam_app(login, password)
        except FileExistsError as err:
            print(err)

    def remove(self, **kwargs):
        """
        Validate params and remove app with given id
        :param kwargs:
        :return:
        """
        super(Steam, self).remove(**kwargs)

        login = kwargs.get('login')
        password = kwargs.get('password')
        try:
            self.remove_steam_app(login, password)
        except FileExistsError as err:
            print(err)

    def install_steam_app(self, login, password):
        """
        Performing installation of a steam app

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
            '+app_update',
            self.ident,
            'validate',
            '+quit',
            '>>',
            progress_file_path
        ]

        start_command = ' '.join(command_elements)
        process= subprocess.Popen(start_command, shell=True, close_fds=True)
        print(
            "Installing app via {platform}. Follow progress at {logfile}".
                format(
                platform=PLATFORM_STEAM,
                logfile=progress_file_path)
        )
        process.communicate()
        print("Finished")
        os.remove(progress_file_path)

    def remove_steam_app(self, login, password):
        """
        Performing removal of a steam app

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
            '+app_uninstall -complete',
            self.ident,
            '+quit',
            '>>',
            progress_file_path
        ]

        remove_command = ' '.join(command_elements)
        process = subprocess.Popen(remove_command, shell=True, close_fds=True)
        print(
            "Removing app via {platform}. Follow progress at {logfile}".format(
                platform=PLATFORM_STEAM,
                logfile=progress_file_path)
        )
        process.communicate()
        print("Finished")
        os.remove(progress_file_path)

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
            'gdebi'
            'steam-launcher',
            'libgl1-mesa-dri:i386',
            'libgl1:i386',
            'libc6:i386',
            'xdg-desktop-portal',
            'xdg-desktop-portal-gtk'
        ]

        return params

    def initialize_platform(self):
        """
        Non-root steps needed for platform initialization
        :return:
        """
        super(Steam, self).initialize_platform()
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

    def activate_platform(self):
        """
        Perform anything needed
        :return:
        """
        self.install_system_dependencies()
        self.install_external_packages()

    def check_user_permission(self):
        """
        Overwrite of default permission set
        Activating needs admin rights
        :return:
        """
        if self.action == ACTION_ACTIVATE:
            self.admin_needed = True
        super(Steam, self).check_user_permission()

    def install_system_dependencies(self):
        """
        Overwriting due to steam package is not in apt-cache
        Performs installation of system packages that is demanded by platform
        :return:
        """
        if os.getuid() != 0:
            raise ValueError(
                "Installing systemdependencies needs root rights. " 
                "Please try 'sudo aptstore-core {platform} {action}' instead".format(
                    platform=self.platform_name,
                    action=ACTION_ACTIVATE,
                )
            )

        cache = apt.cache.Cache()
        cache.update()
        cache.open()

        packages = self.get_platform_dependencies()
        # steam-launcher needs to be downloaded manually
        packages.remove('steam-launcher')
        for pkg_name in packages:
            pkg = cache[pkg_name]
            if not pkg.is_installed:
                pkg.mark_install()
        cache.commit()

    def install_external_packages(self):
        """
        Install external debian packages
        :return:
        """
        for key in self.data['external_packages']:
            package_info = self.data['external_packages'][key]
            if package_info['type'] != 'deb':
                continue
            source = package_info['source']
            target = package_info['target']
            self.download_external_package(source, target)

            command_elements = [
                'gdebi -n',
                target
            ]

            install_command = ' '.join(command_elements)
            process = subprocess.Popen(install_command, shell=True, close_fds=True)

    def download_external_package(self, source, target):
        """
        Downloads from source and place package at target
        :param source:
        :param target:
        :return:
        """
        r = requests.get(source, allow_redirects=True)
        open(target, 'wb').write(r.content)

