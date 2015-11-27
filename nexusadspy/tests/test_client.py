# -*- coding: utf-8 -*-

from __future__ import (
    print_function, division, generators,
    absolute_import, unicode_literals
)

import os

import pytest

from nexusadspy import AppnexusClient
from nexusadspy.exceptions import NexusadspyConfigurationError


def test_failure_no_credentials():
    try:
        os.environ['USERNAME_NEXUSADSPY']
        os.environ['PASSWORD_NEXUSADSPY']
    except KeyError:
        with pytest.raises(NexusadspyConfigurationError):
            AppnexusClient('.appnexus_auth.json')
