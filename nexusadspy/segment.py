
from __future__ import (
    print_function, division, generators,
    absolute_import, unicode_literals
)

from io import BytesIO
from gzip import GzipFile
import time
import logging

from nexusadspy.client import AppnexusClient


class AppnexusSegmentsUploader:

    BATCH_UPLOAD_ANDROID_SPECIFIER = '8'
    BATCH_UPLOAD_IOS_SPECIFIER = '3'

    def __init__(self, users_list, segment_code, separators, member_id,
                 credentials_path='.appnexus_auth.json'):
        """
        Batch-upload API wrapper for AppNexus.
        :param users_list: list, List of dictionaries representing AppNexus users. Every member should have fields
            - uid: AppNexus user ID. AAID/IDFS in case of mobile.
            - timestamp: POSIX timestamp when user entered the segment.
            - expiration (optional): Expiration timestamp for the user. A POSIX timestamp. Defaults to 0.
            - value (optional): Numerical value for the segment. Defaults to 0.
            - mobile_os (optional): OS used by the user. Considered internally by AppNexus to be desktop if absent.
        :param segment_code: str, Segment code to add users to.
        :param separators: list, List of five field separators. As documented in
        https://wiki.appnexus.com/display/api/Batch+Segment+Service+-+File+Format#BatchSegmentService-FileFormat-Separators
        :param member_id: str, Member ID for AppNexus account.
        :param credentials_path: str (optional), Credentials path for AppnexusClient. Defaults to '.appnexus_auth.json'.
        :return:
        """
        self._credentials_path = credentials_path
        self._users_list = users_list
        self._segment_code = segment_code  # Appnexus bug: Segment upload batch API does not work with segment IDs
        self._separators = separators
        self._member_id = member_id
        self._logger = logging.getLogger('nexusadspy.segment')

    def upload(self, polling_duration_sec=2, max_retries=10):
        """
        Initiate segment upload task
        :param polling_duration_sec: int (optional), Time to sleep while polling for status. Defaults to 2.
        :param max_retries: int (optional), Max number of polling retries to be done. Defaults to 10.
        :return: tuple, Tuple with two values, number of valid users and invalid users.
        """
        valid_user_count = invalid_user_count = 0
        api_client = AppnexusClient(self._credentials_path)
        job_id, upload_url = self._initialize_job(api_client)
        self._upload_batch_to_url(api_client, upload_url)
        for attempt in range(max_retries):
            time.sleep(polling_duration_sec)
            job_status = self._get_job_status_response(api_client, job_id)
            if job_status[0].get('phase') == 'completed':
                valid_user_count = job_status[0].get('num_valid_user')
                invalid_user_count = job_status[0].get('num_invalid_user')
                break
        return valid_user_count, invalid_user_count

    def _initialize_job(self, api_client):
        service_endpoint = 'batch-segment?member_id={}'.format(self._member_id)
        response = api_client.request(service_endpoint, 'POST')
        job_id = response[0]['batch_segment_upload_job']['job_id']
        upload_url = response[0]['batch_segment_upload_job']['upload_url']
        return job_id, upload_url

    def _upload_batch_to_url(self, api_client, upload_url):
        upload_buffer = self._get_buffer_for_upload()
        headers = {'Content-Type': 'application/octet-stream'}
        api_client.request(upload_url, 'POST', data=upload_buffer.read(), prepend_endpoint=False, headers=headers)

    def _get_job_status_response(self, api_client, job_id):
        status_endpoint = 'batch-segment?member_id={}&job_id={}'.format(self._member_id, job_id)
        headers = {'Content-Type': 'application/octet-stream'}
        return api_client.request(status_endpoint, 'GET', headers=headers)

    def _get_buffer_for_upload(self):
        upload_string = '\n'.join(self._get_upload_string_for_user(user) for user in self._users_list)
        self._logger.debug("Attempting to upload \n" + upload_string)
        compressed_buffer = BytesIO()
        with GzipFile(fileobj=compressed_buffer, mode='wb') as compressor:
            compressor.write(upload_string.encode('UTF-8'))
        compressed_buffer.seek(0)
        return compressed_buffer

    def _get_upload_string_for_user(self, user):
        upload_string = str(user['uid']) + self._separators[0]
        upload_string += str(self._segment_code) + self._separators[2]
        upload_string += str(user.get('expiration', 0)) + self._separators[2]
        upload_string += str(user['timestamp']) + self._separators[2]
        upload_string += str(user.get('value', 0))
        user_mobile_os = user.get('mobile_os')
        if user_mobile_os is not None:
            if user_mobile_os.lower() == 'android':
                # Appnexus bug: AAID should be uploaded as both IDFA and AAID. Otherwise it cannot be used in mopub.
                upload_string = upload_string + self._separators[4] + self.BATCH_UPLOAD_ANDROID_SPECIFIER +\
                    "\n" + upload_string + self._separators[4] + self.BATCH_UPLOAD_IOS_SPECIFIER
            elif user_mobile_os.lower() == 'ios':
                upload_string = upload_string + self._separators[4] + self.BATCH_UPLOAD_IOS_SPECIFIER
        return upload_string
