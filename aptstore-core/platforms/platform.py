# -*- coding: utf-8 -*-
import os
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
        for key, path in self.data['paths']:
            os.makedirs(path, 0o755)

    def perform_downloads(self):
        """
        Download and optionally extract configured downloads
        :return:
        """
        downloads = self.data['downloads']

        for download in downloads:
            r = requests.get(download['source'], allow_redirects=True)
            open(download['target'], 'wb').write(r.content)
            if download['type'] == 'tarfile':
                tar = tarfile.open(download['targetfile'])
                tar.extractall(path=download['target'])
                tar.close()
