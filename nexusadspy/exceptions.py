# -*- coding: utf-8 -*-

from __future__ import (
    print_function, division, generators,
    absolute_import, unicode_literals
)


class NexusadspyError(Exception):
    pass


class NexusadspyAPIError(NexusadspyError):
    pass


class NexusadspyConfigurationError(NexusadspyError):
    pass
