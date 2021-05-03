# -*- coding: utf-8 -*-
import json
import os.path
import pickle
import re
import sys
import steam.webauth as wa
import tkinter as tk
from tkinter import simpledialog
from . import REPORT_PATH_INSTALLED, REPORT_PATH_PURCHASED
from .reporter import Reporter
from ..platforms import PLATFORM_STEAM


class ReporterSteam(Reporter):
    data = None
    captcha = None
    gui_mode = False
    two_factor_code = None
    session_path = None
    user = None

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

        self.user = wa.WebAuth(self.login)
        self.handle_session_cookie()

        try:
            self.user.login(self.password)
        except (wa.CaptchaRequired, wa.LoginIncorrect) as exp:
            if isinstance(exp, LoginIncorrect):
                print("Abort. Steam password incorrect")

            if isinstance(exp, wa.CaptchaRequired):
                self.solve_captcha(self.user.captcha_url)
                
            self.user.login(password=self.password, captcha=self.captcha)
        except wa.EmailCodeRequired:
            message = (
                "Your account is protected with Steam Guard.\n"
                "A code has been sent to your E-Mail address.\n"
            )
            self.two_factor_input('Enter code: ', message)
            self.user.login(email_code=self.two_factor_code)
        except wa.TwoFactorCodeRequired:
            message = (
                "Your account is protected with Steam Guard.\n"
                "A code has been sent to your mobile.\n"
            )
            self.two_factor_input('Enter code: ', message)
            self.user.login(twofactor_code=self.two_factor_code)

        steam_all_games_url = [
            'http://steamcommunity.com/id/',
            self.login,
            '/games/?tab=all'
        ]
        page = ''.join(steam_all_games_url)
        request_result = self.user.session.get(page)
        site_content = request_result.text
        pattern = '\[{([^\]]+)\]'
        matches = re.findall(pattern, site_content, flags=re.DOTALL)
        result = matches[0]
        games_json = "[{" + result + "]"
        gamedata = json.loads(games_json)

        base_path_parts = [
            self.user_home,
            '/.aptstore/',
            REPORT_PATH_PURCHASED,
            self.platform + '/',
        ]
        base_path = ''.join(base_path_parts)
        for game in gamedata:
            if not game['appid']:
                continue
            path = base_path + str(game['appid']) + '.json'
            fd = open(path, 'w')
            fd.write(json.dumps(game))

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

    def solve_captcha(self, captcha_url):
        """
        Gets the input for solution of captcha. Form depends on the
        GUI-Flag set
        :param captcha_url:
        :return:
        """
        complete_message = "{task}:\n{url}\n{prompt}".format(
            task='Please solve captcha you see at',
            url=captcha_url,
            prompt='Enter solution'
        )

        if self.gui_mode:
            form = tk.Tk()

            window_width = form.winfo_reqwidth()
            window_height = form.winfo_reqheight()
            position_right = int(form.winfo_screenwidth() / 2 - window_width / 2)
            position_down = int(form.winfo_screenheight() / 2 - window_height / 2)
            form.geometry("+{}+{}".format(position_right, position_down))

            form.withdraw()

            self.captcha = simpledialog.askstring(
                "Steam Captcha",
                complete_message
            )
        else:
            print(complete_message)
            self.captcha = input('Enter solution: ')

    def two_factor_input(self, prompt, message):
        """
        Gets an input from user. Depending if gui flag is set
        :return:
        """
        if self.gui_mode:
            form = tk.Tk()

            window_width = form.winfo_reqwidth()
            window_height = form.winfo_reqheight()
            position_right = int(form.winfo_screenwidth() / 2 - window_width / 2)
            position_down = int(form.winfo_screenheight() / 2 - window_height / 2)
            form.geometry("+{}+{}".format(position_right, position_down))

            form.withdraw()

            complete_message = "{message}\n{prompt}".format(
                message=message,
                prompt=prompt
            )

            self.two_factor_code = simpledialog.askstring(
                "Steam Guard",
                complete_message
            )
        else:
            print(message)
            self.two_factor_code = input(prompt + ': ')

    def handle_session_cookie(self):
        """
        Handling persisiting of a steam web session
        :return:
        """
        path = self.session_path + self.platform
        if os.path.isfile(path):
            f = open(path, 'rb')
            self.user.session = pickle.load(f)
        else:
            f = open(path, 'wb')
            pickle.dump(self.user.session, f)
        f.close()
