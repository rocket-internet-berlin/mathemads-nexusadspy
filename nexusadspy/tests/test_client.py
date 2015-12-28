# -*- coding: utf-8 -*-

from __future__ import (
    print_function, division, generators,
    absolute_import, unicode_literals
)

import os

import pytest
from mock import patch

from nexusadspy import AppnexusClient
from nexusadspy.exceptions import NexusadspyConfigurationError


def test_failure_no_credentials():
    try:
        os.environ['USERNAME_NEXUSADSPY']
        os.environ['PASSWORD_NEXUSADSPY']
    except KeyError:
        with pytest.raises(NexusadspyConfigurationError) as excinfo:
            client = AppnexusClient('.appnexus_auth.json')
            client._get_new_auth_token()

            assert 'set environment variables' in str(excinfo.value.lower())


def test_http_methods():
    with patch.object(AppnexusClient, "_do_paged_get", autospec=True) as mock_paged:
        with patch.object(AppnexusClient, "_do_authenticated_request", autospec=True) as mock_auth:
            mock_auth.return_value = (200, {})
            mock_paged.return_value = (200, {})
            clnt = AppnexusClient("foo")
            clnt.request("bar", "get")
            assert mock_auth.call_count == 0
            mock_paged.assert_called_once_with(clnt, clnt.endpoint + "/bar", "get",
                                               data={}, get_field=None, headers=None, params={})

    with patch.object(AppnexusClient, "_do_paged_get", autospec=True) as mock_paged:
        with patch.object(AppnexusClient, "_do_authenticated_request", autospec=True) as mock_auth:
            mock_auth.return_value = (200, {})
            mock_paged.return_value = (200, {})
            clnt = AppnexusClient("bar")
            clnt.request("foo", "post")
            mock_auth.assert_called_once_with(clnt, clnt.endpoint + "/foo", "post",
                                              data={}, headers=None, params={})
            assert mock_paged.call_count == 0

    with patch.object(AppnexusClient, "_do_paged_get", autospec=True) as mock_paged:
        with patch.object(AppnexusClient, "_do_authenticated_request", autospec=True) as mock_auth:
            mock_auth.return_value = (200, {})
            mock_paged.return_value = (200, {})
            clnt = AppnexusClient("pfoo")
            clnt.request("pbar", "put")
            mock_auth.assert_called_once_with(clnt, clnt.endpoint + "/pbar", "put",
                                              data={}, headers=None, params={})
            assert mock_paged.call_count == 0

    with patch.object(AppnexusClient, "_do_paged_get", autospec=True) as mock_paged:
        with patch.object(AppnexusClient, "_do_authenticated_request", autospec=True) as mock_auth:
            mock_auth.return_value = (200, {})
            mock_paged.return_value = (200, {})
            clnt = AppnexusClient("dfoo")
            clnt.request("dbar", "delete")
            mock_auth.assert_called_once_with(clnt, clnt.endpoint + "/dbar", "delete",
                                              data={}, headers=None, params={})
            assert mock_paged.call_count == 0


def test_wrong_http_methods():
    clnt = AppnexusClient("foo")
    with pytest.raises(ValueError) as excinfo:
        clnt.request("bar", "wget")
        assert excinfo.value.lower() == 'Argument "method" must be one of ' \
            '["get", "post", "put", "delete"]. You supplied: "wget".'
