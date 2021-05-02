# -*- coding: utf-8 -*-
""" contents and stat functions """

REPORT_TYPE_PURCHASED = 'purchased'
REPORT_TYPE_INSTALLED = 'installed'
REPORT_TYPE_PROGRESS = 'progress'

REPORT_FOLDER = 'reports/'
REPORT_PATH_PURCHASED = REPORT_FOLDER + REPORT_TYPE_PURCHASED + '/'
REPORT_PATH_INSTALLED = REPORT_FOLDER + REPORT_TYPE_INSTALLED + '/'
REPORT_PATH_PROGRESS = REPORT_FOLDER + REPORT_TYPE_PROGRESS + '/'


def get_available_report_types():
    """
    Returns a config list of report types

    :return: list
    """
    available_types = [
        REPORT_TYPE_PURCHASED,
        REPORT_TYPE_INSTALLED,
        REPORT_TYPE_PROGRESS,
    ]

    return available_types
