# -*- coding: utf-8 -*-
import hashlib
import os
import threading
import subprocess
import apt
from .platform import Platform


class Steam(Platform):
    """
    Steam platform
    """

    def __init__(self):
        super()
        self.data = {
            'paths': {
                'steam': os.path.expanduser('~') + '/.aptstore/steam/',
                'progress': os.path.expanduser('~') + '/.aptstore/progress/',
            },
            'binaries': {
                'steamcmd': os.path.expanduser('~') + '/.aptstore/bin/steamcmd.sh',
            },
            'downloads': {
                'steamcmd': {
                    'source': 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz',
                    'target': os.path.expanduser('~') + '/.aptstore/bin/steamcmd.tar.gz',
                    'targetfile': 'steamcmd.tar.gz',
                    'type': 'tarfile',
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
        appid = kwargs.get('appid')

        trigger_download = threading.Thread(
                target=self.install_steam_app,
                args=(appid, login, password)
        )
        trigger_download.daemon = True
        trigger_download.start()

    def install_steam_app(self, appid, login, password):
        """
        Thread that will be started for performing installation of a steam app

        :param appid:
        :param login:
        :param password:
        :return:
        """
        steamcmd = self.data['binaries']['steamcmd']
        progress_path = self.data['paths']['progress']
        message_output_file = self.get_message_filename(login, appid)
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

    def get_install_params(self):
        """
        Returns list of expected params for a proper installation
        :return: list
        """
        params = [
            'login',
            'password',
            'appid',
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

    def remove(self):
        pass

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
            raise ValueError

        return True

    def check_system_packages(self):
        """
        Checks if all needed system packages are installed
        @todo currently bound to debian only but should work independent
        :return:
        """
        cache = apt.cache.Cache()
        cache.update()
        cache.open()

        packages_to_check = self.get_platform_dependencies()
        for pkg_name in packages_to_check:
            pkg = cache[pkg_name]
            if not pkg.is_installed:
                raise ValueError("Package {pkg_name} not installed".format(pkg.name))

    def activate_platform(self):
        """
        Install needed system dependencies
        :return:
        """

        if os.getuid() != 0:
            raise ValueError(
                "Activating a platform needs root rights." 
                "Please use 'sudo aptstore activate steam' instead"
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

    def get_message_filename(self, user, gameid):
        """
        Returns a unique filename for progress messages

        :param user:
        :param gameid:
        :return:
        """
        game_hash = self.get_md5(user + gameid)
        message_file = [
            game_hash,
            '.txt',
        ]
        message_filename = ''.join(message_file)

        return message_filename

    def get_md5(self, ingoing):
        """
        Returns an md5 hash of ingoing string
        :param ingoing:
        :return:
        """
        m = hashlib.md5()
        m.update(ingoing)
        outgoing = m.hexdigest()

        return str(outgoing)
