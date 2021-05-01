# -*- coding: utf-8 -*-
import os
import subprocess
import time

import apt
import requests
import pexpect
from pexpect import EOF, TIMEOUT

from . import ACTION_ACTIVATE
from . import PLATFORM_STEAM
from .platform import Platform
from ..reporting import REPORT_TYPE_PROGRESS, REPORT_TYPE_PURCHASED, REPORT_TYPE_INSTALLED
from ..reporting.steam import ReporterSteam


class Steam(Platform):
    """
    Steam platform
    """

    def __init__(self, action=None):
        super(Steam, self).__init__(action)
        self.platform_name = PLATFORM_STEAM
        self.data = {
            'paths': {
                'progress': self.user_home + '/.aptstore/progress/',
                'binaries': self.user_home + '/.aptstore/bin/',
            },
            'binaries': {
                'steamcmd': self.user_home + '/.aptstore/bin/steamcmd.sh',
            },
            'downloads': {
                'steamcmd': {
                    'source': 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz',
                    'target': self.user_home + '/.aptstore/bin/steamcmd.tar.gz',
                    'type': 'tarfile',
                    'validate': {
                        'steamcmd': self.user_home + '/.aptstore/bin/steamcmd.sh',
                        'linux32': self.user_home + '/.aptstore/bin/linux32',
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
            self.check_steam_login(login, password)
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
            self.check_steam_login(login, password)
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

        reporter = ReporterSteam()
        reporter.set_app_ident(self.ident)
        reporter.set_file_progress(progress_file_path)

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
            "Install app via {platform}. Follow progress at {logfile}".
                format(
                platform=PLATFORM_STEAM,
                logfile=progress_file_path)
        )

        while process.poll() is None:
            time.sleep(1)
            reporter.create_report(REPORT_TYPE_PROGRESS)
        print("Finished")
        # os.remove(progress_file_path)

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
            "Remove app via {platform}. Follow progress at {logfile}".format(
                platform=PLATFORM_STEAM,
                logfile=progress_file_path
            )
        )

        reporter = ReporterSteam()
        reporter.set_app_ident(self.ident)
        reporter.set_file_progress(progress_file_path)

        while process.poll() is not None:
            time.sleep(1)
            reporter.create_report(REPORT_TYPE_PROGRESS)
            print("Removal is running. Create progress report...")
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
            'gui_mode',
        ]

        return params

    def get_platform_dependencies(self):
        """
        Returns list needed debian packages that need to be installed
        :return: list
        """
        params = [
            'expect',
            'gdebi',
            # 'steam-launcher',
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
        self.activate_i386()
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

    def activate_i386(self):
        """
        Enables 32bit architecture mandatory for steam to work
        :return:
        """
        command_elements = [
            'dpkg',
            '--add-architecture',
            'i386'
        ]

        command = ' '.join(command_elements)
        process = subprocess.Popen(command, shell=True, close_fds=True)

    def check_steam_login(self, login, password):
        """
        Triggers a login via steamcmd for determine if there is some need for
        two factor user validation
        :return:
        """
        print("Validate login to steam...")
        steamcmd = self.data['binaries']['steamcmd']

        command_elements = [
            steamcmd,
            '+login',
            login,
            password,
        ]

        shell_command = ' '.join(command_elements)

        # define expects
        expect_steam_guard = "Steam Guard code"
        expect_steam_captcha = "Please take a look at the captcha image"

        # spawn subshell
        child = pexpect.spawn(shell_command)
        expected_match = child.expect(
            [
                expect_steam_guard,
                expect_steam_captcha,
                'Steam>'
            ]
        )

        try:
            if expected_match == 0:
                child.after
                message = (
                    "Your account is protected with Steam Guard.\n"
                    "A code has been sent to your E-Mail address.\n"
                )
                self.two_factor_input('Enter code: ', message)
                child.sendline(self.two_factor_code)
                child.expect('Steam>')
                child.sendline('quit')
            elif expected_match == 1:
                prompt = child.after
                message = (
                    "Your account is protected with Steam Guard.\n"
                    "Please enter the code of captcha from:\n" + prompt
                )
                self.two_factor_input('Enter code: ', message)
                child.sendline(self.two_factor_code)
                child.expect('Steam>')
                child.sendline('quit')
            elif expected_match == 2:
                print("Steam-Login successful")
                child.sendline('quit')
        except EOF:
            pass
        except TIMEOUT:
            pass

        child.terminate()
