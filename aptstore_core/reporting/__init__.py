# -*- coding: utf-8 -*-
""" contants and stat functions """

REPORT_TYPE_PURCHASED = 'purchased'
REPORT_TYPE_INSTALLED = 'installed'
REPORT_TYPE_PROGRESS = 'progress'


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
