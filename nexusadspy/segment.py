
from __future__ import (
    print_function, division, generators,
    absolute_import, unicode_literals
)

from nexusadspy.client import AppnexusClient
from io import BytesIO
from gzip import GzipFile


class MemberOfSegment:
    """
    Class to hold attributes about the user to be added in segment.
    """
    def __init__(self,appnexus_user_id, timestamp, mobile_os=None, expiration=0, numeric_value=0):
        """
        Detailed documentation about values can be found here:
        https://wiki.appnexus.com/display/api/Batch+Segment+Service+-+File+Format
        :param appnexus_user_id: str, Appnexus ID of the user. IDFA/AAID in case of mobiles.
        :param timestamp: int, Unix timestamp at which user goes into effect in segment.
        :param mobile_os: str, mobile OS used by user. None if desktop.
        :param expiration: int, Lifetime of user in segment (e.g. android, ios). 0 means never expire.
        :param numeric_value: int, Numeric value for the user.
        """
        self._user_id = appnexus_user_id
        self._expiration = expiration
        self._timestamp = timestamp
        self._numeric_value = numeric_value
        self._mobile_os = mobile_os

    def get_user_id(self):
        return self._user_id

    def get_timestamp(self):
        return self._timestamp

    def get_expiration(self):
        return self._expiration

    def get_value(self):
        return self._numeric_value

    def get_mobile_os(self):
        return self._mobile_os


class SegmentsUploaderJob:
    """
    batch-upload API wrapper for appnexus
    """

    BATCH_UPLOAD_ANDROID_SPECIFIER = "8"
    BATCH_UPLOAD_IOS_SPECIFIER = "3"

    def __init__(self, users_list, segment_code, separators, member_id,
                 credentials_path='.appnexus_auth.json'):
        """
        Initialize the uploader
        :param users_list: list, List of MemberOfSegment. Users to be added in segment.
        :param segment_code: str, Segment code to add users in.
        :param separators: array, Array of five field separators. As documented in 
        https://wiki.appnexus.com/display/api/Batch+Segment+Service+-+File+Format#BatchSegmentService-FileFormat-Separators
        :param member_id: str, Member ID for appnexus account.
        :param credentials_path: str, Credentials path for AppnexusClient.
        :return:
        """
        self._appnexus_client = AppnexusClient(credentials_path)
        self._users_list = users_list
        self._segment_code = segment_code  # Appnexus bug: Segment upload batch API does not work with segment IDs
        self._separators = separators
        self._member_id = member_id
        self._job_id = None

    def initialize_upload(self):
        """
        Start upload job for the segment.
        """
        upload_buffer = self._get_buffer_for_upload()
        service_endpoint = 'batch-segment?member_id={}'.format(self._member_id)
        response = self._appnexus_client.request(service_endpoint, "POST")
        self._job_id = response[0]['batch_segment_upload_job']['job_id']
        upload_url = response[0]['batch_segment_upload_job']['upload_url']
        headers = {'Content-Type': 'application/octet-stream'}
        self._appnexus_client.request(upload_url, 'POST', data=upload_buffer.read(), endpoint='', headers=headers)

    def has_upload_completed(self):
        """
        Check status of upload job
        :return: bool, True if it's completed. False otherwise.
        """
        completed = False
        if self._job_id is not None:
            response = self._get_job_status_response()
            if response[0].get('phase') == 'completed':
                completed = True
        return completed

    def get_acceptance_status(self):
        """
        Returns status of the job.
        :return: Tuple of two as (valid users, invalid users). (0, 0) for incomplete job.
        """
        response = self._get_job_status_response()
        valid_user_count = response[0]['batch_segment_upload_job']['num_valid_user']
        invalid_user_count = response[0]['batch_segment_upload_job']['num_invalid_user']
        return valid_user_count, invalid_user_count

    def _get_job_status_response(self):
        status_endpoint = 'batch-segment?member_id={}&job_id={}'.format(self._member_id, self._job_id)
        headers = {u'Content-Type': u'application/octet-stream'}
        return self._appnexus_client.request(status_endpoint, "GET", headers=headers)

    def _get_buffer_for_upload(self):
        upload_string = '\n'.join(self._get_upload_string_for_user(user) for user in self._users_list)
        print(upload_string)
        compressed_buffer = BytesIO()
        with GzipFile(fileobj=compressed_buffer, mode="wb") as compressor:
            compressor.write(upload_string)
        compressed_buffer.seek(0)
        return compressed_buffer

    def _get_upload_string_for_user(self, user):
        upload_string = str(user.get_user_id()) + self._separators[0]
        upload_string += str(self._segment_code) + self._separators[2]
        upload_string += str(user.get_expiration()) + self._separators[2]
        upload_string += str(user.get_timestamp()) + self._separators[2]
        upload_string += str(user.get_value())
        if user.get_mobile_os() is not None:
            if user.get_mobile_os().lower() == 'android':
                # Appnexus bug: AAID should be uploaded as both IDFA and AAID. Otherwise it cannot be used in mopub.
                upload_string = upload_string + self._separators[4] + self.BATCH_UPLOAD_ANDROID_SPECIFIER +\
                    "\n" + upload_string + self._separators[4] + self.BATCH_UPLOAD_IOS_SPECIFIER
            else:
                upload_string = upload_string + self._separators[4] + self.BATCH_UPLOAD_IOS_SPECIFIER
        return upload_string
