# -*- coding: utf-8 -*-
""" contants and stat functions """

ACTION_INSTALL = 'install'
ACTION_REMOVE = 'remove'
ACTION_ACTIVATE = 'activate'

PLATFORM_DEBIAN = 'debian'
PLATFORM_FLATHUB = 'flathub'
PLATFORM_SNAPSTORE = 'snapstore'
PLATFORM_STEAM = 'steam'
PLATFORM_PROTON = 'proton'
PLATFORM_SCRIPT = 'script'


def get_available_platforms():
    """
    Returns a config list of each available platform

    :return: list
    """
    available_platforms = [
        PLATFORM_DEBIAN,
        #PLATFORM_FLATHUB,
        #PLATFORM_SNAPSTORE,
        PLATFORM_STEAM,
        PLATFORM_PROTON,
        #PLATFORM_SCRIPT,
    ]

    return available_platforms

def get_available_actions():
    """
    Returns a config list of available actions

    :return: list
    """
    available_actions = [
        ACTION_INSTALL,
        ACTION_REMOVE,
        ACTION_ACTIVATE,
    ]

    return available_actions
