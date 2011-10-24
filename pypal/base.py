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

from pypal import settings


def ensure_unicode(obj):
    """Encode the given object in unicode - recursively.

    Credit should go out to Ben Darnell for this one since the code
    is a modification of the solution in tornado.

    :param obj: The object to walk through and encode contained values
    """
    if isinstance(obj, (unicode, type(None))):
        return obj

    if isinstance(obj, dict):
        items = obj.iteritems()
        return dict((ensure_unicode(k), ensure_unicode(v)) for k, v in items)
    elif isinstance(obj, (list, tuple)):
        return list(ensure_unicode(i) for i in obj)
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    return None


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
    def __init__(self, raw, shallow, http_error=False):
        """Initialize the response object and convert the shallow
        response dictionary into one that resembling the
        hierarchy set by PayPal.

        :param raw: Unparsed response, i.e raw response body
        :param shallow: The one level deep dictionary retrieved using
                        ``'Client.parse'``
        :param http_error: The HTTPError exception in case it is caught
                           during execution of the request.
        """
        self.raw = raw
        self.shallow = None
        self.http_error = http_error
        if shallow:
            self.shallow = shallow
            self.update(self.construct_hierarchy(shallow))

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

    @property
    def success(self):
        """Check whether the response resembles success or not."""
        if self.http_error:
            return False

        ack = self.get_ack(as_upper=True)
        if not ack:
            return False
        return (ack == ACK_SUCCESS or ack == ACK_SUCCESS_WITH_WARNING)

    @classmethod
    def construct_hierarchy(cls, shallow):
        """Walk the given one level deep dictionary given by our client
        interface and convert it into one that reflects the intended
        hierarchy.

        :param shallow: The shallow dictionary given by the client
                        on response initialization.
        """
        dictionary = {}
        for key, value in shallow.items():
            hierarchy = key.split('.')
            dictionary = cls._recursive_parse(dictionary, hierarchy, value)
        return dictionary

    @classmethod
    def _recursive_parse(cls, result, keys, value):
        """Construct hierarchy for one key in shallow response dictionary.
        PayPal has the standard of naming keys depending on which group
        they belong to - an example::

            responseEnvelope.timestamp

        The hierarchy can go even deeper, one case is when there is an
        error in the request. In those instances PayPal specifies in which
        context certain parameters belongs to. An example of this::

            error(0).parameter(0)
            error(1).domain

        Using these keys in our response dictionary is less than ideal.
        Instead we parse each key in order to detect these patterns
        in order to construct a dictionary which is easier to work with.

        The examples above, along with others, will therefore end up
        in a dictionary resembling the one below::

            {
                'responseEnvelope': {
                    'timestamp': |VALUE|
                },
                error: [
                    {
                        parameter: {
                            0: |FIRST_PARAMETER|,
                            1: |SECOND_PARAMETER|,
                            errorId: |ERROR_ID|
                        },
                        domain: |VALUE|
                    },
                    {
                        parameter: {
                            0: |FIRST_PARAMETER|,
                            1: |SECOND_PARAMETER|,
                            errorId: |ERROR_ID|
                        },
                        domain: |VALUE|
                    }
                ]
            }

        :param result: The dictionary in which all children should
                       be contained
        :param keys: List containing the strings found in one key instance
                     after splitting it by all the dots.
        :param value: The value assigned to the given key
        """
        if not keys:
            if len(value) == 1:
                return value[0]
            return value

        first = keys[0]

        if isinstance(first, basestring) and first[-1] == ')':
            try:
                # Find the first occurence of '(' and construct
                # the list necessary to contain all items associated
                # with that context, i.e having the same context id.
                n_position = first.index('(')
                # Retrieve the context id
                n = int(first[(n_position + 1):-1])
                # Remove context identifier from the current key
                first = first[:n_position]
                # Insert the context identifier amongst the keys to
                # be created in the next depth of the dictionary
                keys.insert(1, n)
            except ValueError:
                pass

        if first not in result:
            result[first] = {}

        result[first] = cls._recursive_parse(result[first], keys[1:], value)
        return result


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

        :param config: Prepared instance of ```settings.Config``` which will
                       take precedence over any key-values given.
        :param kwargs: Key-value pairs which are passed along to a new instance
                       of ```settings.Config``` in case the config argument
                       was not given.
        """
        if not config:
            config = settings.Config(**kwargs)
        else:
            self.config = config

    def call(self, api_group, api_action, endpoint=None, **params):
        """Send an API request.

        :param api_group: Which API group the action belongs to, e.g Permissions
        :param api_action: Which API action within the group to call
        :param endpoint: Override the endpoint which is otherwise determined
                         by the client. Useful in cases where the API group has
                         been issued a unique endpoint.
        :param params: Dictionary containing the key-value pairs required
                       for the given action.
        """
        headers = self.get_headers()
        body = self.prepare(params)

        endpoint = self.config.endpoint if not endpoint else endpoint
        url = endpoint + '/%s/%s' % (api_group, api_action)
        print url

        try:
            request = urllib2.Request(url, body, headers)
            raw_response = urllib2.urlopen(request).read()
            data = self.parse(raw_response)
        except urllib2.HTTPError as e:
            logging.error(e.strerror)
            return Response(None, None, http_error=e)
        return Response(raw_response, data)

    def get_headers(self):
        """Retrieve dictionary containing the necessary HTTP headers
        to set when sending requests to PayPal.

        They contain the credentials required to successfully authenticate
        your application along with what protocol to use.

        """
        ret = {}
        if self.config.application_id:
            ret['X-PAYPAL-APPLICATION-ID'] = self.config.application_id

        if self.config.token_authentication:
            ret['X-PAYPAL-SECURITY-USERID'] = self.config.api_username
            ret['X-PAYPAL-SECURITY-PASSWORD'] = self.config.api_password
            ret['X-PAYPAL-SECURITY-SIGNATURE'] = self.config.api_signature
            ret['X-PAYPAL-REQUEST-DATA-FORMAT'] = self.config.protocol
            ret['X-PAYPAL-RESPONSE-DATA-FORMAT'] = self.config.protocol
            return ret

        # TODO: Implement the authentication method utilizing given
        # certificate instead of using tokens.
        ret['X-PAYPAL-SECURITY-SUBJECT'] = None
        return ret

    def parse(self, raw_response):
        """Trigger the appropriate parse method depending on which protocol
        is being used.

        :param raw_response: The raw string given in the PayPal response
        """
        return self._get_protocol_method(parse_action=True)(raw_response)

    def parse_nvp(self, raw_response):
        """Parse the raw response as NVP data.

        :param raw_response: The raw string given in the PayPal response
        """
        from urlparse import parse_qs
        return parse_qs(raw_response)

    def parse_json(self, raw_response):
        raise NotImplemented()

    def parse_xml(self, raw_response):
        raise NotImplemented()

    def prepare(self, params):
        return self._get_protocol_method(parse_action=False)(params)

    def prepare_nvp(self, params):
        from urllib import urlencode
        return urlencode(params)

    def prepare_xml(self, params):
        raise NotImplemented()

    def prepare_json(self, params):
        raise NotImplemented()

    def _get_protocol_method(self, parse_action=True):
        identifier = 'parse' if parse_action else 'prepare'
        property_reference = '_%s_method' % identifier
        method = getattr(self, property_reference, None)
        if method:
            return method

        if self.config.protocol == settings.NVP_PROTOCOL:
            method = getattr(self, '%s_nvp' % identifier)
        elif self.config.protocol == settings.JSON_PROTOCOL:
            method = getattr(self, '%s_json' % identifier)
        else:
            # PayPal will default to XML in case the protocol
            # is not set accurately. Therefore, we do the same
            # in order to handle the error response correctly.
            method = getattr(self, '%s_xml' % identifier)

        setattr(self, property_reference, method)
        return method
