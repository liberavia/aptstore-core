# -*- coding: utf-8 -*-

import pwd
import grp
import os
import sys
import json
from . import *


class Reporter:
    """
    Class for providing a base interface
    """

    file_progress = None
    file_report = None
    report_type = None

    # user
    sudo_mode = None
    user_name = None
    user_id = None
    group_id = None
    user_home = None

    # progress data
    platform = ''
    app_ident = ''
    app_name = ''
    status = ''
    status_message = ''
    percent_done = 0
    percent_remaining = 0
    download_size = 0
    download_done = 0
    download_rate = 0
    eta = ''

    def __init__(self):
        self.create_paths()
        self.set_user_environment()
        pass

    def set_file_progress(self, path):
        self.file_progress = path

    def set_file_report(self, path):
        self.file_report = path

    def get_file_report(self):
        return self.file_report

    def set_user_environment(self):
        """
        Cares about setting user data even if script is run with sudo
        """
        user_name = os.getenv('SUDO_USER')
        if user_name:
            self.sudo_mode = True
        else:
            self.sudo_mode = False
            user_name = os.getenv('USER')

        self.user_name = str(user_name)
        self.user_id = pwd.getpwnam(self.user_name).pw_uid
        self.group_id = grp.getgrnam(self.user_name).gr_gid
        self.user_home = os.path.expanduser('~' + self.user_name)

    def create_report(self, report_type):
        available = get_available_report_types()

        try:
            available.index(report_type)
        except ValueError:
            print("Abort. Unknown report type.")
            sys.exit(1)

        if report_type == REPORT_TYPE_PROGRESS:
            self.create_progress_report()

        if report_type == REPORT_TYPE_INSTALLED:
            self.create_installed_report()

        if report_type == REPORT_TYPE_PURCHASED:
            self.create_purchased_report()

    def create_progress_report(self, data=None):
        if not data:
            data = self.get_progress_data()

        if not data:
            raise ValueError("No data for creating progress report")
            sys.exit(1)

        json_data = json.dumps(data)
        path = self.get_file_report()

        try:
            with open(path, 'w') as progress_file:
                progress_file.write(json_data)
        except OSError:
            print(
                "Abort. Could not write into progress file:\n"
                "{path}\n".format(path=path)
            )
            sys.exit(1)

    def create_installed_report(self):
        pass

    def create_purchased_report(self):
        pass

    def get_progress_data(self):
        percent_done = "{percent}".format(percent=self.percent_done)
        percent_remaining = "{percent}".format(percent=self.percent_remaining)
        download_size = "{mb}MB".format(mb=self.download_size)
        download_done = "{mb}MB".format(mb=self.percent_done)
        download_rate = "{rate} kB/s".format(rate=self.download_rate)

        progress_data = {
            'platform': self.platform,
            'app_ident': self.app_ident,
            'app_name': self.app_name,
            'status': self.status,
            'status_message': self.status_message,
            'percent_done': percent_done,
            'percent_remaining': percent_remaining,
            'download_size': download_size,
            'download_done': download_done,
            'download_rate': download_rate,
            'eta': self.eta,
        }

        return progress_data

    def create_paths(self):
        """
        create paths needed for reporting
        @todo: Better exception handling
        """
        pathlist = self.get_pathlist

        for path in pathlist:
            try:
                os.makedirs(path, 0o755)
                os.chown(path, self.user_id, self.group_id)
            except FileExistsError:
                pass
            except OSError:
                pass

    def get_pathlist(self):
        """
        Returns pathlist which can be overwritten
        :return:
        """
        base_path = self.user_home + '/.aptstore/'

        pathlist = [
            base_path + 'reports/purchased/',
            base_path + 'reports/installed/',
            base_path + 'reports/progress/',
        ]

        return pathlist
