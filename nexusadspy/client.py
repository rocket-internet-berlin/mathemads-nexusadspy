# -*- coding: utf-8 -*-

from __future__ import (
    print_function, division, generators,
    absolute_import, unicode_literals
)

from collections import defaultdict
import os
import time
import json
import logging

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

try:
    import FileNotFoundError
except ImportError as err:
    FileNotFoundError = IOError

from nexusadspy.exceptions import NexusadspyAPIError, NexusadspyConfigurationError

import requests


logging.basicConfig(level=logging.INFO)


class AppnexusClient():
    endpoint = 'https://api.appnexus.com'

    def __init__(self, path):
        self.path = path
        self.logger = logging.getLogger('AppnexusClient')

    def request(self, service, method, params=None, data=None, headers=None,
                get_field=None, prepend_endpoint=True):
        """
        Sends a request to the Appnexus API. Handles authentication, paging, and throttling.

        :param service: str, One of the services Appnexus services (https://wiki.appnexus.com/display/api/API+Services).
        :param method: str, HTTP method to be used. One of 'GET', 'POST', 'PUT', or 'DELETE'.
        :param params: dict (optional), Any data to be sent in URL as parameters.
        :param data: dict (optional), Any data to be sent in the request.
        :param headers: dict (optional), Any HTTP headers to be sent in the request.
        :return: list, List of response dictionaries.
        """
        method = method.lower()

        params = params or {}
        data = data or {}

        if method not in ['get', 'post', 'put', 'delete']:
            raise ValueError(
                'Argument "method" must be one of '
                '["get", "post", "put", "delete"]. '
                'You supplied: "{}".'.format(method)
            )

        url = urljoin(base=self.endpoint, url=service) if prepend_endpoint else service

        if method == 'get':
            res_code, res = self._do_paged_get(url, method, params=params,
                                               data=data, headers=headers,
                                               get_field=get_field)
        else:
            res_code, res = self._do_authenticated_request(url, method,
                                                           params=params,
                                                           data=data,
                                                           headers=headers)

        self._check_response(res_code, res)

        if not isinstance(res, list):
            res = [res]

        return res

    def _do_paged_get(self, url, method, params=None, data=None, headers=None,
                      start_element=None, batch_size=None, max_items=None,
                      get_field=None):
        res = defaultdict(list)

        if start_element is None:
            start_element = 0
        if batch_size is None:
            batch_size = 100

        while True:
            data.update({'start_element': start_element,
                         'batch_size': batch_size})

            r_code, r = self._do_authenticated_request(url, method, params=params,
                                                       data=data, headers=headers,
                                                       get_field=get_field)

            output_term = get_field or r['dbg_info']['output_term']
            output = r.get(output_term, r)

            if isinstance(output, list):
                res[output_term] += output  # assume list of dictionaries
            else:
                if not isinstance(output, dict):
                    res[output_term].append({output_term: output})
                else:
                    res[output_term].append(output)

            start_element += batch_size

            count = int(r.get('count', 0))
            if len(res[output_term]) >= count:
                break

            if max_items is not None and len(res) >= max_items:
                break

        res = res[output_term]

        return r_code, res

    def _do_throttled_request(self, url, method, params=None, data=None, headers=None,
                              sec_sleep=2., max_failures=100,
                              get_field=None):

        if isinstance(data, dict):
            data = json.dumps(data)
        no_fail = 0
        while True:
            r = requests.request(method, url, params=params, data=data, headers=headers)
            r_code = r.status_code

            try:
                r = r.json()['response']
            except (KeyError, ValueError):
                if len(r.content) > 0:
                    r = self._convert_csv_to_dict(r.content, get_field)
                else:
                    self._check_response(r_code, {})

            if no_fail < max_failures and r.get('error_code', '') == 'RATE_EXCEEDED':
                no_fail += 1
                time.sleep(sec_sleep ** no_fail)
                continue

            return r_code, r

    @staticmethod
    def _convert_csv_to_dict(csv_bytestr, field):
        s = csv_bytestr.decode('utf-8')
        headings, rows = s.split('\r\n')[0], s.split('\r\n')[1:]
        headings = [h.strip() for h in headings.split(',')]
        rows = (r for r in rows if len(r) > 0)
        rows = (r.split(',') for r in rows)
        rows = [[el.strip() for el in r] for r in rows]

        res = [{h: v for h, v in zip(headings, row)} for row in rows]

        return {field: res}

    def _do_authenticated_request(self, url, method, params=None, data=None,
                                  headers=None, get_field=None):
        headers = headers or {}
        headers.update({'Authorization': self._get_auth_token()})

        while True:
            r_code, r = self._do_throttled_request(url, method, params=params,
                                                   data=data, headers=headers,
                                                   get_field=get_field)

            if r.get('error_id', '') == 'NOAUTH':
                headers.update({'Authorization': self._get_auth_token(overwrite=True)})
                continue  # retry with new authorization token

            return r_code, r

    def _get_auth_token(self, overwrite=False):
        if overwrite:
            os.rename(self.path, self.path + '_backup')

        try:
            token = self._get_cached_auth_token()
        except FileNotFoundError:
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

        r_code, r = self._do_throttled_request(url, 'post', data=data, headers=headers)
        token = r['token']

        return token

    def _check_response(self, response_code, response):
        if not isinstance(response, list):
            response = [response]

        for res in response:
            if res.get('error_id') is not None or response_code != 200:
                raise NexusadspyAPIError('Response status code: "{}"'.format(response_code),
                                         res.get('error_id'),
                                         res.get('error'),
                                         res.get('error_description'))
