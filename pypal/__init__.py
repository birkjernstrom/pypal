# -*- coding: utf-8 -*-
"""Implementation of the functionality required to successfully
communicate with the PayPal API suite.

This module is utilized by the adapters which correspond and cover
one API group each.

This package was inspired by the existing paypal package.
However, even though its interface could be utilized to trigger
any given API request, it lacked functions which would ease
implementation of certain API calls.

This package aims to, with time, cover the PayPal API suite completely.
As well as containing functions covering common actions; requiring
a chain of API calls.

"""

import logging
import urllib2

from pypal import settings, util


#: The uppercased value contained in ack on successful responses
ACK_SUCCESS = 'SUCCESS'
#: The uppercased value contained in ack on successful responsed, but
#: which also contains warnings.
ACK_SUCCESS_WITH_WARNING = 'SUCCESSWITHWARNING'
#: The uppercased value contained in ack on responses containing warnings
ACK_WARNING = 'WARNING'
#: The uppercased value contained in ack on failure
ACK_FAILURE = 'FAILURE'
#: The uppercased value contained in ack on failures containing warnings too
ACK_FAILURE_WITH_WARNING = 'FAILUREWITHWARNING'

class Response(dict):
    """Parses the given PayPal response in order to convert it into
    a dictionary which accurately reflects the data hierarchy.

    """
    def __init__(self, raw, response_dict, http_error=False):
        """Initialize the response object and convert the shallow
        response dictionary into one that resembling the
        hierarchy set by PayPal.

        :param raw: Unparsed response, i.e raw response body
        :param response_dict: Prepared dictionary which has been generated
                              by parsing the raw response body.
        :param http_error: The HTTPError exception in case it is caught
                           during execution of the request.
        """
        self.raw = raw
        self.http_error = http_error
        if response_dict:
            self.update(response_dict)

    def get_response_envelope(self):
        """Retrieve the data contained in the response envelope."""
        return self.get('responseEnvelope', None)

    def get_ack(self, as_upper=False):
        """Retrieve the value corresponding to the ack key in the
        response envelope. The contained value contains the data
        required to determine a successful request.

        :param as_upper: Whether to convert the case to upper or not.
        """
        envelope = self.get_response_envelope()
        if not envelope:
            return None

        ack = envelope.get('ack', None)
        if not ack or not as_upper:
            return ack
        return ack.upper()

    def is_success(self):
        """Check whether the response resembles success or not."""
        if self.http_error:
            return False

        ack = self.get_ack(as_upper=True)
        if not ack:
            return False
        return (ack == ACK_SUCCESS or ack == ACK_SUCCESS_WITH_WARNING)

    success = property(is_success)

PAYPAL_BASE_URL = 'https://www.paypal.com'
PAYPAL_SANDBOX_BASE_URL = 'https://www.sandbox.paypal.com'

class Client(object):
    """The client provides an unified interface to communicate with the
    PayPal API without having to deal with the lower-level implementation
    in the callees.

    Depending on configuration it will target the intended endpoint, encode
    given parameters and deal with application authentication.
    """
    def __init__(self, config=None, **kwargs):
        """Initialize a client with the given configurations.
        There is no need for more than one instance of the client
        unless the configuration has to vary.

        :param config: Prepared instance of ``'pypal.settings.Config``` which will
                       take precedence over any key-values given.
        :param kwargs: Key-value pairs which are passed along to a new instance
                       of ``'pypal.settings.Config'`` in case the config argument
                       was not given.
        """
        if not config:
            config = settings.Config(**kwargs)
        else:
            self.config = config

    def call(self, api_group, api_action, endpoint=None, **params):
        """Wrapper of our send method which simplifies URL generation
        depending on intended API group and actions.

        :param api_group: Which API group the action belongs to, e.g Permissions
        :param api_action: Which API action within the group to call
        :param endpoint: Override the endpoint which is otherwise determined
                         by the client. Useful in cases where the API group has
                         been issued a unique endpoint.
        :param params: Dictionary containing the key-value pairs required
                       for the given action.
        """
        endpoint = self.config.endpoint if not endpoint else endpoint
        url = endpoint + '/%s/%s' % (api_group, api_action)

        if 'requestEnvelope' not in params:
            params['requestEnvelope'] = self.config.request_envelope

        try:
            request_body = self.render_request_body(params)

            response = self.send(url, request_body)
            response_body = response.read()
            data = self.parse_response_body(response_body)
        except urllib2.HTTPError as e:
            logging.error(e.strerror)
            return Response(None, None, http_error=e)
        return Response(response_body, data)

    def send(self, url, body=None):
        """Send an API request against given url.

        :param url: The PayPal URL to target
        :param body: The HTTP request body
        """
        headers = self.get_headers()
        request = urllib2.Request(url, body, headers)
        return urllib2.urlopen(request)

    def get_headers(self):
        """Retrieve dictionary containing the necessary HTTP headers
        to set when sending requests to PayPal.

        They contain the credentials required to successfully authenticate
        your application along with specification of which format to utilize.

        """
        ret = {}
        if self.config.application_id:
            ret['X-PAYPAL-APPLICATION-ID'] = self.config.application_id

        if self.config.token_authentication:
            ret['X-PAYPAL-SECURITY-USERID'] = self.config.api_username
            ret['X-PAYPAL-SECURITY-PASSWORD'] = self.config.api_password
            ret['X-PAYPAL-SECURITY-SIGNATURE'] = self.config.api_signature
            ret['X-PAYPAL-REQUEST-DATA-FORMAT'] = self.config.api_format
            ret['X-PAYPAL-RESPONSE-DATA-FORMAT'] = self.config.api_format
            return ret

        # TODO: Implement the authentication method utilizing given
        # certificate instead of using tokens.
        ret['X-PAYPAL-SECURITY-SUBJECT'] = None
        return ret

    def get_paypal_url(self, path):
        base = PAYPAL_SANDBOX_BASE_URL
        if not self.config.in_sandbox:
            base = PAYPAL_BASE_URL
        return base + path

    def parse_response_body(self, response, format=None):
        formatter = self._get_format_method(True, format=format)
        dictionary = formatter(response)
        return util.ensure_unicode(dictionary)

    @classmethod
    def parse_json(cls, response):
        json = get_json_module()
        return json.loads(response)

    def render_request_body(self, params, format=None):
        params = util.ensure_unicode(params)
        formatter = self._get_format_method(False, format=format)
        return formatter(params)

    @classmethod
    def render_json(cls, params):
        json = get_json_module()
        return json.dumps(params)

    def _get_format_method(self, parse_method, format=None):
        if not format:
            format = self.config.api_format

        format = format.lower()
        method_prefixes = ('render', 'parse')
        method_name = '%s_%s' % (method_prefixes[parse_method], format)
        return getattr(self, method_name)


def get_json_module():
    try:
        import json
    except ImportError:
        import simplejson as json
    return json
