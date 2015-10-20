# Nexusadspy

A thin Python wrapper on top of the Appnexus API.

## Example

Set your developer username and password in the environment:

    $ export USERNAME_NEXUSADSPY="..."
    $ export PASSWORD_NEXUSADSPY="..."

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
