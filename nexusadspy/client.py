# -*- coding: utf-8 -*-

from __future__ import (
    print_function, division, generators,
    absolute_import, unicode_literals
)

import os
import time
from urllib.parse import urlencode, urljoin
import json
import logging

from nexusadspy.exceptions import NexusadspyAPIError, NexusadspyConfigurationError

import requests


logging.basicConfig(level=logging.INFO)


class AppnexusClient():
    endpoint = 'https://api.appnexus.com'

    def __init__(self, path):
        self.path = path
        self.logger = logging.getLogger('AppnexusClient')

    def request(self, service, method, data=None, headers=None):
        """

        :param query: dict
        :param field: str
        :return: pandas Dataframe
        """
        method = method.lower()
        service = service.lower()

        assert method in ['get', 'post', 'put', 'delete']

        url = urljoin(base=self.endpoint, url=service)

        if method == 'get':
            res = self._do_paged_get(url, method, data, headers)
        else:
            res = self._do_throttled_request(url, method, data, headers)

        return res

    def _do_paged_get(self, url, method, data=None, headers=None,
                      start_element=None, batch_size=None, max_items=None):

        data = data or {}
        res = []

        if start_element is None:
            start_element = 0
        if batch_size is None:
            batch_size = 100

        while True:
            data.update({'start_element': start_element,
                         'batch_size': batch_size})

            r = self._do_authenticated_request(url, method, data, headers)

            output_term = r['dbg_info']['output_term']
            for item in r[output_term]:
                res.append(item)

            start_element += batch_size

            count = int(r.get('count'))
            if len(res) >= count:
                break

            if max_items is not None and len(res) >= max_items:
                break

        return res

    def _do_throttled_request(self, url, method, data=None, headers=None,
                              sec_sleep=2., max_failures=100):
        params = urlencode(data)
        data = json.dumps(data)
        no_fail = 0
        while True:
            r = requests.request(method, url, params=params, data=data, headers=headers)

            if r.status_code != 200:
                raise NexusadspyAPIError(r.json())

            r = r.json()['response']

            if no_fail < max_failures and r.get('error_code', '') == 'RATE_EXCEEDED':
                no_fail += 1
                time.sleep(sec_sleep**no_fail)
                continue

            self._check_response(r)

            return r

    def _do_authenticated_request(self, url, method, data=None, headers=None):
        headers = headers or {}
        headers.update({'Authorization': self._get_auth_token()})

        while True:
            r = self._do_throttled_request(url, method, data, headers)

            if r.get('error_code', '') == 'NOAUTH':
                headers.update({'Authorization': self._get_auth_token(overwrite=True)})
                continue  # retry with new authorization token

            return r

    def _get_auth_token(self, overwrite=False):
        if overwrite:
            os.rename(self.path, self.path + '_backup')

        try:
            token = self._get_cached_auth_token()
        except (FileNotFoundError, IOError):
            token = self._get_new_auth_token()
            self._cache_auth_token(token)
        return token

    def _cache_auth_token(self, token):
        with open(self.path, 'w') as f:
            json.dump({'token': token}, f)

    def _get_cached_auth_token(self):
        with open(self.path, 'r') as f:
            auth = json.load(f)
            return auth['token']

    def _get_new_auth_token(self):
        try:
            username = os.environ['USERNAME_NEXUSADSPY']
            password = os.environ['PASSWORD_NEXUSADSPY']
        except KeyError as e:
            raise NexusadspyConfigurationError(
                'Set environment variables "USERNAME_NEXUSADSPY" and '
                '"PASSWORD_NEXUSADSPY" appropriately. '
                'You failed to set: "{}".'.format(e.args[0])
            )

        data = {'auth': {'username': username, 'password': password}}
        headers = {'Content-type': 'application/json; charset=UTF-8'}
        url = urljoin(base=self.endpoint, url='auth')

        r = self._do_throttled_request(url, 'post', data, headers)
        token = r['token']

        return token

    def _check_response(self, response):
        if response.get('error_id') is not None:
            raise NexusadspyAPIError(response.get('error_id'),
                                     response.get('error'),
                                     response.get('error_description'))
