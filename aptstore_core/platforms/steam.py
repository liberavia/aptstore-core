# -*- coding: utf-8 -*-
import glob
import os
import subprocess
import time
from pathlib import Path

import apt
import pexpect
import requests
from pexpect import EOF, TIMEOUT

from . import ACTION_ACTIVATE
from . import PLATFORM_STEAM
from .platform import Platform
from ..reporting import REPORT_TYPE_INSTALLED, REPORT_TYPE_PURCHASED, REPORT_PATH_PURCHASED
from ..reporting import REPORT_TYPE_PROGRESS, REPORT_PATH_INSTALLED
from ..reporting.steam import ReporterSteam


class Steam(Platform):
    """
    Steam platform
    """

    def __init__(self, **kwargs):
        super(Steam, self).__init__(**kwargs)
        self.set_login(kwargs.get('login'))
        self.set_password(kwargs.get('password'))
        self.set_reporter(ReporterSteam(
            login=self.login,
            password=self.password,
            gui_mode=self.gui_mode
        ))
        self.platform_name = PLATFORM_STEAM
        self.data = {
            'paths': {
                'purchased': self.user_home + '/.aptstore/purchased/steam/',
                'installed': self.user_home + '/.aptstore/installed/steam/',
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
        try:
            self.platform_initialized()
        except ValueError:
            self.initialize_platform()

    def validate_params(self, entered_params, expected_params):
        """
        Validates parameters
        :param entered_params:
        :param expected_params:
        :return:
        """
        super(Steam, self).validate_params(entered_params, expected_params)

        if not self.login or not self.password:
            raise ValueError("Steam needs login data")

    def install(self, **kwargs):
        """
        Validate params and install app with given id
        :param kwargs:
        :return:
        """
        super(Steam, self).install(**kwargs)
        try:
            self.check_steam_login()
            self.install_steam_app()
        except FileExistsError as err:
            print(err)

    def remove(self, **kwargs):
        """
        Validate params and remove app with given id
        :param kwargs:
        :return:
        """
        super(Steam, self).remove(**kwargs)

        try:
            self.check_steam_login()
            self.remove_steam_app()
        except FileExistsError as err:
            print(err)

    # noinspection PyTypeChecker
    def install_steam_app(self):
        """
        Performing installation of a steam app
        :return:
        """
        steamcmd = self.data['binaries']['steamcmd']
        progress_path = self.data['paths']['progress']
        progress_file = self.get_progress_filename(userident=self.login, appident=self.ident)
        progress_file_path = os.path.join(progress_path, progress_file)

        if os.path.isfile(progress_file_path):
            raise FileExistsError("Process already running. Abort.")

        self.reporter.set_app_ident(self.ident)
        self.reporter.set_file_progress(progress_file_path)

        command_elements = [
            'unbuffer',
            steamcmd,
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
                    platform=PLATFORM_STEAM,
                    logfile=progress_file_path
            )
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

    # noinspection PyTypeChecker
    def remove_steam_app(self):
        """
        Performing removal of a steam app
        :return:
        """
        steamcmd = self.data['binaries']['steamcmd']
        progress_path = self.data['paths']['progress']
        progress_file = self.get_progress_filename(userident=self.login, appident=self.ident)
        progress_file_path = os.path.join(progress_path, progress_file)

        if os.path.isfile(progress_file_path):
            raise FileExistsError("Process already running. Abort.")

        command_elements_start = [
            steamcmd,
            '+login',
            self.login,
            self.password,
        ]
        Path(progress_file_path).touch()
        progress_file = open(progress_file_path, 'w+')
        print(
            "Remove app via {platform}. Follow progress at {logfile}".format(
                platform=self.platform_name,
                logfile=progress_file_path
            )
        )
        self.reporter.set_app_ident(self.ident)
        self.reporter.set_file_progress(progress_file_path)

        expect_prompt = 'Steam>'
        command_start = ' '.join(command_elements_start)

        try:
            child = pexpect.spawn(command_start)
            child.expect(expect_prompt)
            progress_file.write("Successfully logged in")
            command_elements_remove_app = [
                'app_uninstall',
                '-complete',
                self.ident,
            ]
            command_remove_app = ' '.join(command_elements_remove_app)
            child.sendline(command_remove_app)
            after = child.after
            child.expect(expect_prompt)
            print("App removed: " + self.ident)
            progress_file.write("App removed: " + self.ident)
            child.sendline('apps_installed')
            child.expect(expect_prompt)
            child.sendline('quit')
            child.terminate()
        except EOF:
            print("EOF")
        except TIMEOUT:
            print("Timeout")
            progress_file.write("Timeout")

        print("Finished")
        try:
            progress_file.close()
            os.remove(progress_file_path)
        except FileNotFoundError:
            pass
        self.reporter.delete_report()
        self.update_installed_apps()

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
        self.update_installed_apps()
        self.update_purchased_apps()

    # noinspection PyTypeChecker
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

        # cache for installed apps built at least once
        try:
            self.check_installed_apps()
        except FileNotFoundError:
            raise ValueError("Cache for installed steam apps not created")

        # cache for purchased apps built at least once
        try:
            self.check_purchased_apps()
        except FileNotFoundError:
            raise ValueError("Cache for purchased steam apps not created")

    # noinspection PyTypeChecker
    def check_installed_apps(self):
        installed_file = self.get_installed_filename(userident=self.login)
        path = self.data['paths']['progress']
        installed_filepath = os.path.join(path, installed_file)
        if not os.path.isfile(installed_filepath):
            raise FileNotFoundError

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
            subprocess.Popen(install_command, shell=True, close_fds=True)

    @staticmethod
    def download_external_package(source, target):
        """
        Downloads from source and place package at target
        :param source:
        :param target:
        :return:
        """
        r = requests.get(source, allow_redirects=True)
        open(target, 'wb').write(r.content)

    @staticmethod
    def activate_i386():
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
        subprocess.Popen(command, shell=True, close_fds=True)

    # noinspection PyTypeChecker
    def update_installed_apps(self):
        """
        Updates raw list
        :return:
        """
        steamcmd = self.data['binaries']['steamcmd']
        progress_path = self.data['paths']['progress']
        installed_file = self.get_installed_filename(userident=self.login)
        installed_file_path = os.path.join(progress_path, installed_file)

        # refresh caches
        cache_path = str(
            self.user_home +
            '/.aptstore/' +
            REPORT_PATH_INSTALLED +
            'steam/'
        )
        self.reporter.delete_cache(cache_path)

        command_elements = [
            'unbuffer',
            steamcmd,
            '+login',
            self.login,
            self.password,
            '+apps_installed',
            '+quit',
            '>',
            installed_file_path
        ]

        start_command = ' '.join(command_elements)
        process = subprocess.Popen(start_command, shell=True, close_fds=True)
        print(
            "Updating cache of installed apps for {platform} at {cachefile}".format(
                platform=PLATFORM_STEAM,
                cachefile=cache_path
            )
        )
        process.communicate()
        self.reporter.set_file_progress(installed_file_path)
        self.reporter.create_report(REPORT_TYPE_INSTALLED)
        print("Finished cache update")

    def check_steam_login(self):
        """
        Triggers a login via steamcmd for determining if there is some need for
        two factor user validation
        :return:
        """
        print("Validate login to steam...")
        steamcmd = self.data['binaries']['steamcmd']

        command_elements = [
            steamcmd,
            '+login',
            self.login,
            self.password,
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
                after = child.after
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

    def update_purchased_apps(self):
        """
        Trigger update of purchased steam apps
        :return:
        """
        cache_path = str(
            self.user_home +
            '/.aptstore/' +
            REPORT_PATH_PURCHASED +
            self.platform_name + '/'
        )
        print(
            "Updating cache of purchased apps for {platform} at {cachefile}".format(
                platform=PLATFORM_STEAM,
                cachefile=cache_path
            )
        )
        self.reporter.delete_cache(cache_path)
        self.reporter.create_report(REPORT_TYPE_PURCHASED)

    def check_purchased_apps(self):
        """
        Check if there is an existing cache for purchased steam apps
        :return:
        """
        check_path = self.data['paths']['purchased']
        check_pattern = '*.json'
        files = glob.glob(check_path + check_pattern)
        if len(files) == 0:
            raise FileNotFoundError
