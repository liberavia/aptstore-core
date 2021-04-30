# -*- coding: utf-8 -*-
import os
import sys
import apt
from apt.progress import base, text
from . import PLATFORM_DEBIAN
from .platform import Platform


class Debian(Platform):
    """
    Debian platform
    """
    apt_cache = None
    progress_acquire = None
    progress_install = None

    def __init__(self, action=None):
        super(Debian, self).__init__(action)
        self.platform_name = PLATFORM_DEBIAN
        self.admin_needed = True
        self.data = {
            'paths': {
                'progress': os.path.expanduser('~') + '/.aptstore/progress/',
            },
        }

    def install(self, **kwargs):
        """
        Validate params and install app with given id
        :param kwargs:
        :return:
        """
        super(Debian, self).install(**kwargs)
        self.initialize_platform()

        try:
            self.platform_initialized()
            expected_params = self.get_install_params()
            self.validate_params(kwargs.keys(), expected_params)
        except ValueError:
            return

        try:
            self.install_debian_app()
        except FileExistsError as err:
            print(err)

    def remove(self, **kwargs):
        """
        Validate params and remove app with given id
        :param kwargs:
        :return:
        """
        super(Debian, self).remove(**kwargs)
        self.initialize_platform()

        try:
            self.remove_debian_app()
        except FileExistsError as err:
            print(err)
            sys.exit("Installation locked")
        except ValueError as err:
            print(err)
            sys.exit("Abort")

    def install_debian_app(self):
        if not self.package_exists():
            raise ValueError(
                "Package '{p}' not found in cache".format(p=self.ident)
            )

        pkg = self.apt_cache[self.ident]
        if pkg.is_installed:
            raise ValueError(
                "Package '{p}' is already installed".format(p=pkg.name)
            )

        pkg.mark_install()
        print("Install package {p}".format(p=pkg.name))
        pkg.commit(self.progress_acquire, self.progress_install)
        # self.follow_progress(pkg)

    def remove_debian_app(self):
        if not self.package_exists():
            raise ValueError(
                "Package '{p}' not found in cache!".format(p=self.ident)
            )

        pkg = self.apt_cache[self.ident]
        if not pkg.is_installed:
            raise ValueError(
                "Package '{p}' is not installed. ".format(p=pkg.name) +
                "So it cannot be removed!"
            )

        pkg.mark_delete()
        print("Remove package {p}".format(p=pkg.name))
        pkg.commit(self.progress_acquire, self.progress_install)
        # self.follow_progress(pkg)

    def follow_progress(self, pkg):
            while not self.progress_acquire.current_bytes < self.progress_acquire.total_bytes:
                pass

            print(self.action + " " + self.ident + "...")
            while not self.progress_install.finish_update():
                percent_installed = self.progress_install.percent
                print(percent_installed)

    def initialize_platform(self):
        """
        Non-root steps needed for platform initialization
        :return:
        """
        super(Debian, self).initialize_platform()
        progress_path = self.data['paths']['progress']
        progress_file = self.get_progress_filename(appident=self.ident)
        progress_file_path = os.path.join(progress_path, progress_file)
        print(progress_file_path)
        fp = open(progress_file_path, 'w')
        self.progress_acquire = text.AcquireProgress(fp)
        self.progress_install = base.InstallProgress()
        self.update_cache()

    def update_cache(self):
        """
        Update apt cache and initialize apt_cache attribute
        :return:
        """
        print("Updating apt cache...")
        self.apt_cache = apt.cache.Cache()
        self.apt_cache.update()
        self.apt_cache.open()

    def package_exists(self):
        """
        Checking if a ident package exists
        :return:
        """
        if not self.apt_cache[self.ident]:
            return False
        return True


