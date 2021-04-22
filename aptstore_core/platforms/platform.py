# -*- coding: utf-8 -*-
import os
import apt
import hashlib
import requests
import tarfile

MESSAGE_NOT_YET_IMPLEMENTED = "WARNING: Needed functionality not yet implemented for current platform!"


class Platform:
    """
    Base class for inheritance for defining a minimum set of available methods
    """

    data = None

    def __init__(self):
        self.data = {}

    def activate_platform(self):
        pass

    def install(self, **kwargs):
        return MESSAGE_NOT_YET_IMPLEMENTED

    def remove(self, **kwargs):
        return MESSAGE_NOT_YET_IMPLEMENTED

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

    def get_message_filename(self, userident, appident):
        """
        Returns a unique filename for progress messages

        :param userident:
        :param appident:
        :return:
        """
        ingoing = str(userident + appident)
        app_hash = self.get_md5(ingoing=ingoing)
        message_file = [
            app_hash,
            '.txt',
        ]
        message_filename = ''.join(message_file)

        return message_filename

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
