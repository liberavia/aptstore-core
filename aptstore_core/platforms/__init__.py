# -*- coding: utf-8 -*-
""" aptstore-core platforms package """

ACTION_INSTALL = 'install'
ACTION_REMOVE = 'remove'
ACTION_ACTIVATE = 'activate'

PLATFORM_DEBIAN = 'debian'
PLATFORM_FLATHUB = 'flathub'
PLATFORM_SNAPSTORE = 'snapstore'
PLATFORM_STEAM = 'steam'
PLATFORM_PROTON = 'proton'
PLATFORM_SCRIPT = 'script'
PLATFORM_STEAMOS = 'steamos'
"""
@todo: PLATFORM_STEAMOS_NODE is only needed temporary until distro determination works reliable 
"""
PLATFORM_STEAMOS_NODE = 'steamdeck'


def get_available_platforms():
    """
    Returns a config list of each available platform

    :return: list
    """
    available_platforms = [
        PLATFORM_DEBIAN,
        # PLATFORM_FLATHUB,
        # PLATFORM_SNAPSTORE,
        PLATFORM_STEAM,
        PLATFORM_PROTON,
        # PLATFORM_SCRIPT,
        PLATFORM_STEAMOS,
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
