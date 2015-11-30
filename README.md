# Nexusadspy

A thin Python wrapper on top of the Appnexus API.

## Status

[![Build Status](https://travis-ci.org/mathemads/nexusadspy.svg)](https://travis-ci.org/mathemads/nexusadspy)
[![Coverage Status](https://coveralls.io/repos/mathemads/nexusadspy/badge.svg?branch=devel&service=github)](https://coveralls.io/github/mathemads/nexusadspy?branch=devel)

## Installation

    pip install nexusadspy

## Examples

Set your developer username and password in the environment:

    $ export USERNAME_NEXUSADSPY="..."
    $ export PASSWORD_NEXUSADSPY="..."

### Sample API service query

Pick one of the Appnexus services to interact with off
[this list](https://wiki.appnexus.com/display/api/API+Services).

Here we will query the API for a list of all our advertisers and we
will store temporarily our authentication token in a hidden file
`.appnexus_auth.json`:

    from nexusadspy import AppnexusClient
    client = AppnexusClient('.appnexus_auth.json')
    r = client.request('advertiser', 'GET')

To download data on just one of your advertisers, simply pass their ID
in the request:

    r = client.request('advertiser', 'GET', data={'id': 123456})

### Sample reporting query

In the following example we set up an `attributed_conversions` report
for the period starting on Oct 1, 2015 and ending on Nov 1, 2015 
for the advertiser with ID `123456`.

    from nexusadspy import AppnexusReport

    columns = ["datetime",
               "pixel_name",
               "pixel_id",
               "post_click_or_post_view_conv",
               "line_item_name",
               "line_item_id",
               "campaign_id",
               "imp_time",
               "advertiser_id"]

    report_type = "attributed_conversions"

    filters = [{"imp_type_id":{"operator":"!=","value": 6}}]

    report = AppnexusReport(advertiser_ids=123456,
                            start_date='2015-10-01',
                            end_date='2015-11-01',
                            filters=filters,
                            report_type=report_type,
                            columns=columns)

To trigger and download the report just run the `get` method on your `report`:

    output_json = report.get()

In case you have `pandas` installed you can also request the report as a
dataframe as follows:

    output_df = report.get(format_='pandas')

### Sample segments upload

In the following example, we upload a list of users to user segment `my_segment_code`
using the [batch segment upload service](https://wiki.appnexus.com/display/api/Batch+Segment+Service).
We assume that the segment `my_segment_code` has already been created in the corresponding account.
The respective users also need to be pixelled on AppNexus from your website before they can be added to segments.

    from nexusadspy.segment import AppnexusSegmentsUploader

    # List of five separators obtained from Appnexus support
    my_separators_list = [':',';','^','~',',']

    seg_code = "my_segment_code"
    my_member_id = "1234"

    members = [
        {"uid": "0123456789012345678", "timestamp": "1447952642"},
        {"uid": "9876543210987654321", "timestamp": "1447921128"},
        {"uid": "1122334455667788990", "timestamp": "1447914439"}
    ]

    uploader = AppnexusSegmentsUploader(members, seg_code, my_spearators_list, my_member_id)

To trigger the upload, run `upload()` method on `uploader`:

    upload_status = uploader.upload()
