# -*- coding: utf-8 -*-
import re
import sys
import json

from .reporter import Reporter
from ..platforms import PLATFORM_STEAM


class ReporterSteam(Reporter):

    def __init__(self):
        super(ReporterSteam, self).__init__()
        self.platform = PLATFORM_STEAM

    def get_pathlist(self):
        """
        Returns pathlist which can be overwritten
        :return:
        """
        pathlist = super(ReporterSteam, self).get_pathlist()
        base_path = self.user_home + '/.aptstore/'

        pathlist.append(base_path + 'reports/purchased/steam/', )
        pathlist.append(base_path + 'reports/installed/steam/', )
        pathlist.append(base_path + 'reports/progress/steam/', )

        return pathlist

    def set_progress_data(self):
        """
        Read from raw progress file and fetch,calculate
        and assign all available data from it.
        :return:
        """
        super(ReporterSteam, self).set_progress_data()
        latest_progress = self.get_latest_progress_message()
        self.filter_progress_data(latest_progress)

    def filter_progress_data(self, line):
        line = line.lstrip()
        if not line:
            print("No progress data to filter")
        if line.startswith('Loading Steam API'):
            self.status_message = 'Loading Steam API...'
        if line.startswith('Logging in user'):
            self.status_message = 'Logging in user...'
        if line.startswith('Logged in'):
            self.status_message = 'Logged in'
        if line.startswith('Waiting for user info'):
            self.status_message = 'Waiting for user info...'

        if line.startswith('Update state (0x3)'):
            self.status_message = 'Reconfiguring...'

        if line.startswith('Update state (0x5)'):
            self.status_message = 'Verifying install...'

        if line.startswith('Update state (0x11)'):
            self.status_message = 'Reallocating install...'

        if line.startswith('Update state (0x61)'):
            self.status_message = 'Downloading...'
            pattern = "downloading, progress: ([0-9.]+) \(([0-9]+) \/ ([0-9]+)"
            matches = re.findall(pattern, line, re.DOTALL)
            pattern_finished = "(fully installed)"
            matches_finished = re.findall(pattern_finished, line, re.DOTALL)
            try:
                matches_finished = matches_finished[0]
            except IndexError:
                matches_finished = ''
            try:
                matches = list(matches[0])
            except IndexError:
                matches = ['', '', '']
            try:
                self.parse_download_percent(matches[0], matches_finished)
                self.parse_download_totals(matches[1], 'downloaded')
                self.parse_download_totals(matches[2], 'todownload')
                self.calculate_speed()
            except IndexError:
                print("Ran into index error!")
                sys.exit(1)

    def parse_download_percent(self, match_value, match_finished):
        """
        Parse percent values
        :param match_value:
        :param match_finished:
        :return:
        """
        try:
            percent_float = float(match_value.replace(",", "."))
            self.percent_done = int(round(percent_float, 0))
        except ValueError:
            self.percent_done = 0

        if match_finished == 'fully installed':
            self.status_message = "Fully installed"
            self.percent_done = 100

        self.percent_remaining = 100 - self.percent_done

    def parse_download_totals(self, match_value, match_type):
        """
        Parse total download values
        :param match_value:
        :param match_type:
        :return:
        """
        try:
            bytes = int(match_value)
            kbytes = float(bytes / 1024)
            mbytes = float(kbytes / 1024)
            megabytes = int(round(mbytes, 0))
            if match_type == 'todownload':
                self.download_size_kbytes = int(kbytes)
                self.download_size = megabytes

            if match_type == 'downloaded':
                self.download_done_kbytes = int(kbytes)
                self.download_done = megabytes
        except ValueError:
            self.download_size = 0
            self.download_done = 0

    def calculate_speed(self):
        with open(self.file_report, 'r') as report_file:
            json_report = json.loads(report_file.read())
            report_file.close()
        if json_report:
            download_done_before = int(json_report['download_done_kbytes'])
            download_done_now = self.download_done_kbytes
            download_delta = download_done_now - download_done_before
            self.download_rate = download_delta