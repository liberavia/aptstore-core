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
    download_size_kbytes = 0
    download_done = 0
    download_done_kbytes = 0
    download_rate = 0
    eta = ''

    def __init__(self):
        self.set_user_environment()
        self.create_paths()
        pass

    def set_app_ident(self, ident):
        self.app_ident = ident

    def set_file_progress(self, path):
        self.file_progress = path

    def set_file_report(self):
        if not self.app_ident:
            raise ValueError('Abort. Cannot set report file without ident')
            sys.exit(1)
        if not self.user_home:
            raise ValueError('Abort. Cannot set report file without user home')
            sys.exit(1)

        base_path = self.user_home + '/.aptstore/'

        file_report_path = ''
        if self.report_type == REPORT_TYPE_PROGRESS:
            file_report_path = base_path + REPORT_PATH_PROGRESS + self.platform + '/'

        file_report_path += self.app_ident
        file_report_path += ".json"

        self.file_report = file_report_path

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

    def create_report(self, report_type, app_ident=None):
        """
        Create report of defined report_type
        :param report_type:
        :param app_ident:
        :return:
        """
        available = get_available_report_types()
        try:
            available.index(report_type)
        except ValueError:
            print("Abort. Unknown report type.")
            sys.exit(1)
        self.report_type = report_type

        if app_ident:
            self.set_app_ident(str(app_ident))
        self.set_file_report()

        if report_type == REPORT_TYPE_PROGRESS:
            self.create_progress_report()

        if report_type == REPORT_TYPE_INSTALLED:
            self.create_installed_report()

        if report_type == REPORT_TYPE_PURCHASED:
            self.create_purchased_report()

    def create_progress_report(self, data=None):
        if not data:
            self.set_progress_data()
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

    def set_progress_data(self):
        """
        Read from raw progress file and fetch,calculate
        and assign all available data from it.
        :return:
        """
        if not self.file_progress:
            raise ValueError('Abort. Cannot create progress data without source')
            sys.exit(1)
        self.status_message = 'Working...'

    def get_progress_data(self):
        percent_done = "{percent}".format(percent=self.percent_done)
        percent_remaining = "{percent}".format(percent=self.percent_remaining)
        download_size = "{mb}MB".format(mb=self.download_size)
        download_done = "{mb}MB".format(mb=self.download_done)
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
            'download_size_kbytes': self.download_size_kbytes,
            'download_done': download_done,
            'download_done_kbytes': self.download_done_kbytes,
            'download_rate': download_rate,
            'eta': self.eta,
        }

        return progress_data

    def create_paths(self):
        """
        create paths needed for reporting
        @todo: Better exception handling
        """
        pathlist = self.get_pathlist()

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
            base_path + REPORT_PATH_PURCHASED,
            base_path + REPORT_PATH_INSTALLED,
            base_path + REPORT_TYPE_PROGRESS,
        ]

        return pathlist

    def get_latest_progress_message(self):
        """
        Reads latest message from raw progress file
        :return:
        """
        progress_file_handler = open(self.file_progress, 'r')
        latest_message = self.tail(progress_file_handler, 1)
        progress_file_handler.close()
        try:
            parsed_message = latest_message[0]
        except:
            parsed_message = ''

        return parsed_message

    def tail(self, filehandler, n, offset=0):
        """
        Reads n lines from filehandler with an offset of offset lines
        :param filehandler:
        :param n:
        :param offset:
        :return:
        """
        avg_line_length = 74
        to_read = n + offset
        while 1:
            try:
                filehandler.seek(-(avg_line_length * to_read), 2)
            except IOError:
                filehandler.seek(0)
            pos = filehandler.tell()
            lines = filehandler.read().splitlines()
            if len(lines) >= to_read or pos == 0:
                return lines[-to_read:offset and -offset or None]
            avg_line_length *= 1.3