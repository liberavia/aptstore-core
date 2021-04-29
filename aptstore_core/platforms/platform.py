# -*- coding: utf-8 -*-
import os
import sys

import apt
import hashlib
import requests
import tarfile
import tkinter
from . import ACTION_ACTIVATE, ACTION_INSTALL, ACTION_REMOVE


class Platform:
    """
    Base class for inheritance for defining a minimum set of available methods
    """

    data = None
    platform_name = None
    action = None
    ident = None
    admin_needed = None
    gui_mode = None
    two_factor_code = None

    def __init__(self, action=None):
        # admin_needed defaulted to False
        self.action = action
        self.admin_needed = False
        self.gui_mode = False
        self.data = {}

    def activate_platform(self):
        self.action = ACTION_ACTIVATE

    def install(self, **kwargs):
        self.action = ACTION_INSTALL
        self.ident = kwargs.get('ident')
        self.gui_mode = kwargs.get('gui_mode')
        try:
            self.check_user_permission()
        except PermissionError as err:
            print(err)
            sys.exit("Wrong permissions")
        print("Permissions valid")
        try:
            self.platform_initialized()
            expected_params = self.get_install_params()
            self.validate_params(kwargs.keys(), expected_params)
        except ValueError as err:
            print(err)
            sys.exit("Initialization problems")
        print("Platform initialized")

    def remove(self, **kwargs):
        self.action = ACTION_REMOVE
        self.ident = kwargs.get('ident')
        self.gui_mode = kwargs.get('gui_mode')
        try:
            self.check_user_permission()
        except PermissionError as err:
            print(err)
            sys.exit("Wrong permissions")
        print("Permissions valid")
        try:
            self.platform_initialized()
            expected_params = self.get_install_params()
            self.validate_params(kwargs.keys(), expected_params)
        except ValueError as err:
            print(err)
            sys.exit("Initialization problems")
        print("Platform initialized")

    def validate_params(self, entered_params, expected_params):
        """
        Validates parameters
        :param entered_params:
        :param expected_params:
        :return:
        """
        if list(set(entered_params).difference(expected_params)):
            inv = ','.join(list(set(entered_params).difference(expected_params)))
            raise ValueError('Unexpected arg(s) {} in kwargs'.format(inv))
        pass

    def create_paths(self):
        """
        creates configured pathes
        :return:
        """
        pathlist = self.data['paths']
        for key, path in pathlist.items():
            try:
                os.makedirs(path, 0o755)
            except FileExistsError:
                pass

    def perform_downloads(self):
        """
        Download and optionally extract configured downloads
        :return:
        """
        downloads = self.data['downloads']

        for key, download in downloads.items():
            try:
                self.validate_download(download)
            except ValueError:
                continue
            r = requests.get(download['source'], allow_redirects=True)
            open(download['target'], 'wb').write(r.content)
            if download['type'] == 'tarfile':
                target_path = download['target']
                target_folder = os.path.dirname(target_path)
                tar = tarfile.open(target_path)
                tar.extractall(path=target_folder)
                tar.close()
                os.remove(target_path)

    def validate_download(self, download):
        """
        Checks if all configured files and or directories are available
        If this is the case raise a ValueError
        :param download:
        :return:
        """
        check_paths = download['validate']

        for key, value in check_paths.items():
            not_existing = (
                not os.path.isfile(value) and
                not os.path.isdir(value)
            )
            if not_existing:
                return

        raise ValueError('Already downloaded that one. skip')

    def get_md5(self, ingoing):
        """
        Returns an md5 hash of ingoing string
        :param ingoing:
        :return:
        """
        m = hashlib.md5()
        m.update(ingoing.encode('utf-8'))
        outgoing = m.hexdigest()

        return str(outgoing)

    def get_progress_filename(self, appident, userident=None):
        """
        Returns a unique filename for progress messages

        :param userident:
        :param appident:
        :return:
        """
        progress_file = [
            self.platform_name,
            appident,
        ]
        if userident != None:
            progress_file.append(userident)

        progress_filename = '_'.join(progress_file)
        progress_filename += '.log'

        return progress_filename

    def check_system_packages(self):
        """
        Checks if all needed system packages are installed
        @todo currently bound to debian only but should work independent
        :return:
        """
        cache = apt.cache.Cache()
        cache.open()

        packages_to_check = self.get_platform_dependencies()
        for pkg_name in packages_to_check:
            pkg = cache[pkg_name]
            if not pkg.is_installed:
                raise ValueError("Package {pkg_name} not installed".format(pkg_name=pkg.name))

    def install_system_dependencies(self):
        """
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
        for pkg_name in packages:
            pkg = cache[pkg_name]
            if not pkg.is_installed:
                pkg.mark_install()
        cache.commit()

    def check_user_permission(self):
        print("Check user permissions...")
        if os.getuid() != 0 and self.admin_needed:
            raise PermissionError(
                "Action needs administrative permission.\n" 
                "Please try 'sudo aptstore-core {platform} {action} {ident}' instead".format(
                    platform=self.platform_name,
                    action=self.action,
                    ident=self.ident
                )
            )
        if os.getuid() == 0 and not self.admin_needed:
            raise PermissionError(
                "Root rights are not allowed for action!\n" 
                "Please try 'aptstore-core {platform} {action} {ident}' instead".format(
                    platform=self.platform_name,
                    action=self.action,
                    ident=self.ident
                )
            )

    def platform_initialized(self):
        """
        Check if all needed elements for platform are available
        :return:
        """
        pass

    def initialize_platform(self):
        """
        Non-root steps needed for platform initialization
        :return:
        """
        try:
            self.check_user_permission()
        except PermissionError as err:
            print(err)
            sys.exit("Wrong permissions")

    def get_install_params(self):
        """
        Returns list of expected params for a proper installation
        :return: list
        """
        params = [
            'platform',
            'action',
            'ident',
            'gui_mode',
        ]

        return params

    def get_platform_dependencies(self):
        """
        Returns list needed debian packages that need to be installed
        :return: list
        """
        params = []

        return params

    def get_two_factor_input(self, prompt, message):
        """
        Gets an input from user. Depending if gui flag is set
        :return:
        """
        if self.gui_mode:
            pass
            form = tkinter.Tk()
            form.title("Two-Factor-Authentication")
            tkinter.Label(form, text=message).grid(row=0, columnspan=2)
            tkinter.Label(form, text=prompt).grid(row=1, column=0)
            entry_field = tkinter.Entry(form)
            entry_field.grid(row=1, column=1)
            button_quit = tkinter.Button(form, text='Quit', command=form.quit).grid(row=3, column=0, sticky=W, pady=4)
            button_ok = tkinter.Button(form, text='OK', command=self.set_two_factor_code).grid(row=3, column=1, sticky=W, pady=4)
            button_ok.bind("<Return>", self.set_two_factor_code)
            tkinter.mainloop()
        else:
            print(message)
            self.two_factor_code = input(prompt + ': ')

    def set_two_factor_code(self, entry_field):
        self.two_factor_code = entry_field.get()
