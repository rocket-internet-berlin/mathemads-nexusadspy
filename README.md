# Nexusadspy

A thin Python wrapper on top of the Appnexus API.

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
for the period starting 01/Oct/2015 to 01/Nov/2015 
for the advertiser with the ID `123456`.

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
