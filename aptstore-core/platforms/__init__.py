# -*- coding: utf-8 -*-
""" contants and stat functions """


def get_available_platforms():
    """
    Returns a config list of each available platform

    :return: dictionary
    """
    available_platforms = {
        "debian": {},
        "flathub": {},
        "snapstore": {},
        "steam": {},
        "proton": {},
        "script": {},
    }

    return available_platforms
