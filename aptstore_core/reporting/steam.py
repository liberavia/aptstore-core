# -*- coding: utf-8 -*-
import json
import re
import sys
import requests

from . import REPORT_PATH_INSTALLED
from .reporter import Reporter
from ..platforms import PLATFORM_STEAM

DEFAULT_STEAM_API_KEY='FCB473938C6B101A6F419003638923D9'


class ReporterSteam(Reporter):
    data = None
    gui_mode = False
    session_path = None

    def __init__(self, **kwargs):
        super(ReporterSteam, self).__init__(**kwargs)
        self.platform = PLATFORM_STEAM
        self.set_login(kwargs.get('login'))
        self.set_password(kwargs.get('password'))
        self.gui_mode = kwargs.get('gui_mode')
        self.session_path = kwargs.get('session_path')

    def create_installed_report(self):
        """
        Creates report of installed steam apps
        :return:
        """
        super(ReporterSteam, self).create_installed_report()
        self.delete_cache(REPORT_PATH_INSTALLED)

        report_file = open(self.file_progress, 'r')
        for line in report_file:
            self.app_ident = None
            self.app_name = None
            self.parse_installed_line(line)
            self.write_installed_cache_for_app()

    def create_purchased_report(self):
        """
        Creates report of games the user has purchased
        :return:
        """
        if not self.login or not self.password:
            print("Cannot create purchase report. No login data")
            return

        steam_games = self.get_steam_games()
        base_path = self.get_purchased_path()

        for game in steam_games:
            if not game['appid']:
                continue
            path = base_path + str(game['appid']) + '.json'
            fd = open(path, 'w')
            fd.write(json.dumps(game))
            fd.close()

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
        """
        Filter progress data from raw output
        :param line:
        :return:
        """
        line = line.lstrip()
        if not line:
            print("No progress data to filter")
        if line.startswith('Deleting in progress'):
            self.status_message = 'Deleting app...'
            self.percent_done = 100
            self.download_done = 'N/A'
            self.download_size = 'N/A'
            self.download_rate = 'N/A'
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
            bytes_amount = int(match_value)
            kbytes = float(bytes_amount / 1024)
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
        """
        Calculates speed by comparing recent and current
        downloaded kBytes
        :return:
        """
        with open(self.file_report, 'r') as report_file:
            json_report = json.loads(report_file.read())
            report_file.close()
        if json_report:
            download_done_before = int(json_report['download_done_kbytes'])
            download_done_now = self.download_done_kbytes
            download_delta = download_done_now - download_done_before
            self.download_rate = download_delta

    def parse_installed_line(self, line):
        """
        Parses line of raw installed progress file and
        fetch needed values from it
        :param line:
        :return:
        """
        pattern = 'AppID ([0-9]+) : "([A-za-z0-9 ]+)"'
        matches = re.findall(pattern, line, re.DOTALL)
        try:
            matches = list(matches[0])
        except IndexError:
            matches = []

        if len(matches) == 2:
            self.app_ident = matches[0]
            self.app_name = matches[1]

    def write_installed_cache_for_app(self):
        """
        Create cache file for current app ident
        :return:
        """
        self.set_file_report()
        app_file = open(self.file_report, 'w')
        app_data = {
            'platform': self.platform,
            'app_ident': self.app_ident,
            'app_name': self.app_name,
        }
        json_data = json.dumps(app_data)
        app_file.write(json_data)
        app_file.close()

    def get_steam_games(self):
        """
        Returns list of available steam games via steam api
        :return:
        """
        steamid = self.get_steam_id()
        steam_games_url = (
            "https://api.steampowered.com/"
            "IPlayerService/GetOwnedGames/v0001/"
            "?key={}&steamid={}&format=json&include_appinfo=1"
            "&include_played_free_games=1".format(
                DEFAULT_STEAM_API_KEY, steamid
            )
        )
        response = requests.get(steam_games_url)
        if response.status_code > 400:
            print("Failed requesting games: {resp}".format(resp=response))
            return []
        json_data = response.json()
        response = json_data['response']
        if not response:
            print("No games found at: {url}".format(url=steam_games_url))
            return []
        if 'games' in response:
            return response['games']
        if 'game_count' in response and response['game_count'] == 0:
            return []
        print("No gamedata found in: {json_data}".format(json_data=json_data))
        return []

    def get_steam_id(self):
        url = 'http://steamcommunity.com/id/{login}'.format(login=self.login)
        result = requests.get(url)
        site_content = result.text
        pattern = '\"steamid\":\"([0-9]+)\"'
        matches = re.findall(pattern, site_content, flags=re.DOTALL)
        steamid = matches[0]

        return steamid
