import copy
import demistomock as demisto
from CommonServerPython import *  # noqa # pylint: disable=unused-wildcard-import
from CommonServerUserPython import *  # noqa

# IMPORTS
from datetime import datetime
import requests

# Disable insecure warnings
requests.packages.urllib3.disable_warnings()

XSOHR_TYPES_TO_CROWDSTRIKE = {
    'account': "username",
    'domain': "domain",
    'email': "email_address",
    'file md5': "hash_md5",
    'file sha-256': "hash_sha256",
    'ip': "ip_address",
    'registry key': "registry",
    'url': "url"
}
CROWDSTRIKE_TO_XSOHR_TYPES = {
    'username': 'Account',
    'domain': 'Domain',
    'email_address': 'Email',
    'hash_md5': 'File MD5',
    'hash_sha256': 'File SHA-256',
    'registry': 'Registry Key',
    'url': 'URL',
    "ip_address": 'IP'
}


class Client(BaseClient):

    def __init__(self, client_id, client_secret, base_url, verify=True, proxy=False):
        self._client_id = client_id
        self._client_secret = client_secret
        self._verify_certificate = verify
        self._base_url = base_url
        super().__init__(
            base_url=base_url,
            verify=self._verify_certificate,
            ok_codes=tuple(),
            proxy=proxy
        )
        self._token = self._get_access_token()
        self._headers = {'Authorization': 'Bearer ' + self._token}

    def http_request(self, method, url_suffix=None, full_url=None, headers=None, params=None, data=None,
                     timeout=10, auth=None) -> dict:

        return super()._http_request(
            method=method,
            url_suffix=url_suffix,
            full_url=full_url,
            headers=headers,
            params=params,
            data=data,
            timeout=timeout,
            auth=auth
        )

    def _get_access_token(self):
        body = {
            'client_id': self._client_id,
            'client_secret': self._client_secret
        }
        token_res = self.http_request(
            method='POST',
            url_suffix='/oauth2/token',
            data=body,
            auth=(self._client_id, self._client_secret)
        )
        return token_res.get('access_token')

    def set_last_run(self):
        current_time = datetime.now()
        current_timestamp = datetime.timestamp(current_time)
        timestamp = str(int(current_timestamp))
        demisto.setIntegrationContext({'last_modified_time': timestamp})
        demisto.info(f'set last_run: {timestamp}')

    def get_last_run(self) -> str:
        if last_run := demisto.getIntegrationContext().get('last_modified_time'):
            demisto.info(f'get last_run: {last_run}')
            params = f'last_updated:>{last_run}'
            self.set_last_run()
        else:
            params = ''
            self.set_last_run()
        return params

    def get_indicators(self, type=None, malicious_confidence='', filter='', q='',
                       limit: int = 200, offset: int = 0, include_deleted=False,
                       get_indicators_command=False) -> Dict[str, Any]:
        if type:
            type_fql = self.build_type_fql(type)
            filter = f'{type_fql}+{filter}' if filter else type_fql

        if malicious_confidence:
            malicious_confidence_fql = f"malicious_confidence:'{malicious_confidence}'"
            filter = f"{malicious_confidence_fql}+{filter}" if filter else malicious_confidence_fql

        if not get_indicators_command:
            if last_run := self.get_last_run():
                filter = f'{last_run}+{filter}' if filter else last_run
                self.set_last_run()

        demisto.info(f' filter {filter}')
        params = assign_params(include_deleted=include_deleted, limit=limit, offset=offset, q=q, filter=filter)

        response = self.http_request(
            method='GET',
            params=params,
            headers=self._headers,
            url_suffix='intel/combined/indicators/v1'
        )
        return response

    def build_type_fql(self, types_list: list) -> str:
        """Builds an indicator type query for the query"""

        if 'ALL' in types_list:
            # Replaces "ALL" for all types supported on XSOAR.
            crowdstrike_types = ['username', 'domain', 'email_address', 'hash_md5', 'hash_sha256', 'ip_address',
                                 'registry', 'url']
            crowdstrike_types = [f"type:'{type}'" for type in crowdstrike_types]

        else:
            crowdstrike_types = [f"type:'{XSOHR_TYPES_TO_CROWDSTRIKE.get(type.lower(), type)}'" for type in types_list]

        result = ','.join(crowdstrike_types)
        return result


def fetch_indicators(client: Client, tlp_color, include_deleted, type, malicious_confidence, filter, q, limit):
    """ fetch indicators from the Crowdstrike Intel

    Args:
        client: Client object
        tlp_color (str): Traffic Light Protocol color.
        include_deleted (bool): include deleted indicators. (send just as parameter)
        type (list): type indicator.
        malicious_confidence(str): medium, low, high
        filter (str): indicators filter.
        q (str): generic phrase match
        limit (int): max num of indicators to fetch

    Returns:
        list of indicators(list)
    """
    raw_response = client.get_indicators(
        type=type,
        malicious_confidence=malicious_confidence,
        filter=filter, q=q,
        include_deleted=include_deleted,
        get_indicators_command=False,
        limit=limit
    )
    parsed_indicators = []  # type: List
    indicator = {}  # type: Dict
    for resource in raw_response['resources']:
        indicator = {
            'type': CROWDSTRIKE_TO_XSOHR_TYPES.get(resource.get('type'), resource.get('type')),
            'value': resource.get('indicator'),
            'rawJSON': resource,
            'fields': {
                'tags': [label.get('name') for label in resource.get('labels')]  # type: ignore
            }
        }
        if tlp_color:
            indicator['fields']['trafficlightprotocol'] = tlp_color
        parsed_indicators.append(indicator)

    return parsed_indicators


def crowdstrike_indicators_list_command(client: Client, args: dict) -> CommandResults:
    """ Gets indicator from Crowdstrike Intel to readable output

    Args:
        client: Client object
        args: demisto.args()

    Returns:
        readable_output, raw_response
    """
    include_deleted = argToBoolean(args.get('include_deleted', False))
    type_ = argToList(args.get('type'))
    malicious_confidence = args.get('malicious_confidence')
    filter = args.get('filter')
    q = args.get('generic_phrase_match')
    offset = int(args.get('offset', 0))
    limit = int(args.get('limit', 50))

    raw_response = client.get_indicators(
        type=type_,
        malicious_confidence=malicious_confidence,
        filter=filter, q=q,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
        get_indicators_command=True
    )
    indicators_list = raw_response.get('resources')
    if outputs := copy.deepcopy(indicators_list):
        for indicator in outputs:
            indicator['type'] = CROWDSTRIKE_TO_XSOHR_TYPES.get(indicator['type'], indicator['type'])
            indicator['published_date'] = timestamp_to_datestring(indicator['published_date'])
            indicator['last_updated'] = timestamp_to_datestring(indicator['last_updated'])
            indicator['value'] = indicator['indicator']
            indicator['labels'] = [label.get('name') for label in indicator.get('labels')]
            del indicator['indicator']
            del indicator['relations']
            del indicator['_marker']

        readable_output = tableToMarkdown(name='Indicators from CrowdStrike Falcon Intel', t=outputs,
                                          headers=["type", "value", "id"], headerTransform=pascalToSpace)

        return CommandResults(
            outputs=outputs,
            outputs_prefix='CrowdStrikeFalconIntel.Indicators',
            outputs_key_field='id',
            readable_output=readable_output,
            raw_response=raw_response
        )
    else:
        return CommandResults(
            readable_output='No Indicators.',
            raw_response=raw_response
        )


def test_module(client: Client, args: dict) -> str:
    try:
        client.get_indicators(limit=1)
    except Exception:
        raise Exception("Could not fetch CrowdStrike Indicator Feed\n"
                        "\nCheck your API key and your connection to CrowdStrike.")
    return 'ok'


def reset_last_run():
    """
    Reset the last run from the integration context
    """
    demisto.setIntegrationContext({})
    return CommandResults(readable_output='Fetch history deleted successfully')


''' MAIN FUNCTION '''


def main() -> None:
    params = demisto.params()
    client_id = params.get('client_id')
    client_secret = params.get('client_secret')
    proxy = params.get('proxy', False)
    verify_certificate = not demisto.params().get('insecure', False)
    base_url = "https://api.crowdstrike.com/"
    tlp_color = params.get('tlp_color')
    include_deleted = argToBoolean(params.get('include_deleted', False))
    type = argToList(params.get('type'))
    malicious_confidence = params.get('malicious_confidence')
    filter = params.get('filter')
    q = params.get('q')
    max_fetch = params.get('max_indicator_to_fetch') if params.get('max_indicator_to_fetch') else 500
    command = demisto.command()
    args = demisto.args()

    demisto.info(f'Command being called is {demisto.command()}')
    demisto.debug(f'Command being called is {demisto.command()}')
    try:
        client = Client(
            client_id=client_id,
            client_secret=client_secret,
            base_url=base_url,
            verify=verify_certificate,
            proxy=proxy
        )

        if command == 'test-module':
            # This is the call made when pressing the integration Test button.
            result = test_module(client, args)
            return_results(result)

        elif command == 'fetch-indicators':
            indicators = fetch_indicators(
                client=client,
                tlp_color=tlp_color,
                include_deleted=include_deleted,
                type=type,
                malicious_confidence=malicious_confidence,
                filter=filter, q=q,
                limit=max_fetch,
            )
            # we submit the indicators in batches
            for b in batch(indicators, batch_size=2000):
                demisto.createIndicators(b)

        elif command == 'crowdstrike-indicators-list':
            return_results(crowdstrike_indicators_list_command(client, args))

        elif command == "crowdstrike-reset-fetch-indicators":
            return_results(reset_last_run())

    # Log exceptions and return errors
    except Exception as e:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute {demisto.command()} command.\nError:\n{str(e)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
