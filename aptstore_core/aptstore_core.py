# -*- coding: utf-8 -*-
from . import platforms
from .platforms.steam import Steam
from .platforms.proton import Proton
from .platforms.debian import Debian
import sys


class AptStoreCore:
    platform_name = None
    platform = None
    action = None
    ident = None
    login = None
    password = None
    gui_mode = False

    def __init__(self, platform, action):
        self.set_action(action)
        self.set_platform(platform)
        self.login = ""
        self.password = ""

    def set_platform(self, platform):
        """
        Validate and set platform that action will be performed on
        :param platform:
        :return:
        """
        try:
            self.validate_platform(platform)
            self.platform_name = platform
        except ValueError:
            sys.exit("Abort. Unknown platform")

        if platform == platforms.PLATFORM_STEAM:
            self.platform = Steam(self.action)

        if platform == platforms.PLATFORM_PROTON:
            self.platform = Proton(self.action)

        if platform == platforms.PLATFORM_DEBIAN:
            self.platform = Debian(self.action)

    def set_action(self, action):
        try:
            self.validate_action(action)
            self.action = action
        except ValueError:
            sys.exit("Abort. Unknown action")

    def set_login(self, login):
        self.login = login

    def set_password(self, password):
        self.password = password

    def set_ident(self, ident):
        """
        Set ident part related to platform and action
        @todo: Validate ident to be valid and save against abuse!
        :param ident:
        :return:
        """
        self.ident = ident

    def set_gui_mode(self):
        self.gui_mode = True

    def validate_platform(self, platform):
        available_platforms = platforms.get_available_platforms()

        if platform not in available_platforms:
            raise ValueError(
                "Platform {platform} not available".format(platform=platform)
            )

    def validate_action(self, action):
        available_actions = platforms.get_available_actions()
        if action not in available_actions:
            raise ValueError(
                "Action {action} not available".format(action=action)
            )

    def trigger_action(self):
        if self.action == platforms.ACTION_INSTALL:
            if self.login:
                self.platform.install(
                    platform=self.platform_name,
                    action=self.action,
                    ident=self.ident,
                    login=self.login,
                    password=self.password,
                    gui_mode=self.gui_mode,
                )
            else:
                self.platform.install(
                    platform=self.platform_name,
                    action=self.action,
                    ident=self.ident,
                    gui_mode=self.gui_mode,
                )
        if self.action == platforms.ACTION_REMOVE:
            if self.login:
                self.platform.remove(
                    platform=self.platform_name,
                    action=self.action,
                    ident=self.ident,
                    login=self.login,
                    password=self.password,
                    gui_mode=self.gui_mode,
                )
            else:
                self.platform.remove(
                    platform=self.platform_name,
                    action=self.action,
                    ident=self.ident,
                    gui_mode=self.gui_mode,
                )
        if self.action == platforms.ACTION_ACTIVATE:
                self.platform.activate_platform()
