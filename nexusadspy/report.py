# -*- coding: utf-8 -*-

from __future__ import (
    print_function, division, generators,
    absolute_import, unicode_literals
)

from datetime import datetime
import time

from nexusadspy import AppnexusClient
from nexusadspy.exceptions import NexusadspyAPIError


class AppnexusReport():
    def __init__(self, report_type, columns, timezone='CET', filters=None,
                 groups=None, start_date=None, end_date=None, report_interval=None,
                 advertiser_ids=None, publisher_ids=None,
                 credentials_path='.appnexus_auth.json',
                 max_retries=100, retry_seconds=2.):
        """
        AppNexus reporting class.

        :param report_type: str
        :param columns: list
        :param timezone: str
        :param filters: list
        :param groups: list
        :param start_date: str
        :param end_date: str
        :param report_interval: str
        :param advertiser_ids: int
        :param publisher_ids: int
        :param credentials_path: str
        :param max_retries: int
        :param retry_seconds: float
        :return:
        """

        if not isinstance(columns, list):
            raise ValueError('"columns" is expected as a list, you '
                             'provided "{}"'.format(columns))

        self.report_type = report_type
        self.columns = columns
        self.timezone = timezone
        self.filters = filters or []
        self.groups = groups or []
        self.start_date = self._format_date(start_date)
        self.end_date = self._format_date(end_date)
        self.report_interval = report_interval
        self.advertiser_ids = advertiser_ids or []
        self.publisher_ids = publisher_ids or []
        self.credentials_path = credentials_path
        self.max_retries = max_retries
        self.retry_seconds = retry_seconds

        self.request = self._build_request()
        self.endpoint = self._build_endpoint()

        self._handle_network_user_request()

    def get(self, format_='json'):
        """
        Trigger and download the report.

        :param format_: optional, Specify 'pandas' to get report as a DataFrame.
        :return:
        """
        client = AppnexusClient(self.credentials_path)
        response = self._post_request(client)
        report_id = response['report_id']

        report = self._get_report(client, report_id)

        if format_ == 'pandas':
            report = self._convert_to_dataframe(report)

        return report

    def _post_request(self, client):
        response = client.request(self.endpoint, 'POST', data=self.request)

        return response[0]

    def _get_report(self, client, report_id):
        self._poll_and_wait(client, report_id)  # block until report ready
        report = self._download_report(client, report_id)

        return report

    def _poll_and_wait(self, client, report_id):
        response = {}
        for retry in range(self.max_retries):
            data = {'id': report_id}
            response = client.request(self.endpoint, 'GET', data=data)[0]
            execution_status = self._get_report_execution_status(response, report_id)
            if execution_status == 'ready':
                response = client.request(self.endpoint, 'GET', data=data, get_field='report')
                break
            else:
                time.sleep(self.retry_seconds**retry)

        if retry == self.max_retries - 1:
            raise NexusadspyAPIError('Report with ID "{}" not ready. '
                                     'Last response was "{}".'.format(report_id,
                                                                      response))

    @staticmethod
    def _get_report_execution_status(response, report_id):
        try:
            return response['execution_status']
        except KeyError:
            report = AppnexusReport._get_report_dict(response['reports'], report_id)
            return report['execution_status']

    @staticmethod
    def _get_report_dict(reports, report_id):
        for report in reports:
            if report['id'] == report_id:
                return report

    @staticmethod
    def _convert_to_dataframe(report):
        import pandas as pd

        return pd.DataFrame(report)

    @staticmethod
    def _download_report(client, report_id):
        report = client.request('report-download', 'GET', get_field='report',
                                params={'id': report_id})

        return report

    @staticmethod
    def _format_date(date_string):
        try:
            datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                date_string = datetime.strptime(date_string, "%Y-%m-%d")
                date_string = date_string.strftime("%Y-%m-%d %H:%M:%S")
            except:
                raise ValueError('Expected data format is YYYY-MM-DD. You '
                                 'provided "{}".'.format(date_string))
        except TypeError:
            pass

        return date_string

    def _build_request(self):
        r = self._get_request_skeleton()
        r = self._add_request_date(r)
        r = self._add_request_filters(r)
        r = self._add_request_groups(r)

        return r

    def _get_request_skeleton(self):
        r = {
            'report': {
                'special_pixel_reporting': False,
                'report_type': self.report_type,
                'timezone': self.timezone,
                'columns': self.columns
            }
        }

        return r

    def _add_request_date(self, r):
        if self.start_date and self.end_date:
            r['report']['start_date'] = self.start_date
            r['report']['end_date'] = self.end_date
        elif self.report_interval:
            r['report_interval'] = self.report_interval
        else:
            r['report_interval'] = 'lifetime'

        return r

    def _add_request_filters(self, r):
        r['report']['filters'] = self.filters

        return r

    def _add_request_groups(self, r):
        r['report']['groups'] = self.groups

        return r

    @staticmethod
    def _build_endpoint():
        return 'report'

    def _handle_network_user_request(self):
        if self.advertiser_ids and self.publisher_ids:
            raise ValueError('As a network user you can request '
                             'advertiser-level and publisher-level reports '
                             'but not both at the same time. You provided '
                             '"advertiser_ids={}" and "publisher_ids={}".'.format(self.advertiser_ids,
                                                                                  self.publisher_ids))

        if self.advertiser_ids:
            self._amend_request('advertiser_id', self.advertiser_ids)
            self._amend_endpoint('advertiser_id', self.advertiser_ids)
        elif self.publisher_ids:
            self._amend_request('publisher_id', self.publisher_ids)
            self._amend_endpoint('publisher_id', self.publisher_ids)

    def _amend_request(self, identifier, items):
        if identifier not in self.request['report']['columns']:
            self.request['report']['columns'].append(identifier)

        self.request['report']['filters'].append({identifier: items})

    def _amend_endpoint(self, identifier, items):
        pass
