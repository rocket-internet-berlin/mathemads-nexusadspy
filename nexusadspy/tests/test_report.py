# -*- coding: utf-8 -*-

from __future__ import (
    print_function, division, generators,
    absolute_import, unicode_literals
)

import pytest

from nexusadspy import AppnexusReport


def test_init_report():
    with pytest.raises(ValueError) as excinfo:
        AppnexusReport("foo", "one")
        assert excinfo.value.lower() == '"columns" is expected as a list, you provided "one"'

    rep = AppnexusReport("foo", ["one"])
    assert rep.endpoint == "report"
    assert rep.request == {
        'report': {
            'columns': ['one'],
            'filters': [],
            'groups': [],
            'report_type': 'foo',
            'special_pixel_reporting': False,
            'timezone': 'CET'
        },
        'report_interval': 'lifetime'}
