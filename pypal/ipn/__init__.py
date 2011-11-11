# -*- coding: utf-8 -*-

import logging
from pypal import Response, Client, util
from pypal import nvp

VERIFICATION_RESPONSE = 'VERIFIED'

EVENT_ADAPTIVE = 'Adaptive Payment PAY'
EVENT_INVALID_NOTIFICATION = 'Invalid-notification'

MODULE_MAPPING = {EVENT_ADAPTIVE: 'pay'}

PRODUCTION_ENDPOINT = 'https://www.paypal.com'
SANDBOX_ENDPOINT = 'https://www.sandbox.paypal.com'

def parse(request_body):
    assert request_body
    return nvp.parse(request_body)


class Listener(object):
    def __init__(self, client):
        self.callbacks = {}
        self.client = client

    def add(self, event_name, callback):
        if event_name not in self.callbacks:
            self.callbacks[event_name] = []
        self.callbacks[event_name].append(callback)

    def trigger(self, event_name, *args, **kwargs):
        callbacks = self.callbacks.get(event_name, None)
        if not callbacks:
            return True

        for callback in callbacks:
            callback(*args, **kwargs)

    def verify(self, request_body):
        endpoint = (PRODUCTION_ENDPOINT, SANDBOX_ENDPOINT)
        endpoint = endpoint[int(self.client.config.in_sandbox)]

        url = endpoint + '/cgi-bin/webscr'
        body = 'cmd=_notify-validate&%s' % request_body

        response = self.client.send(url, body)
        http_code = response.getcode()
        raw_response = response.read()

        if http_code == 200 and raw_response == VERIFICATION_RESPONSE:
            return True

        self.trigger(EVENT_INVALID_NOTIFICATION,
                     http_code,
                     request_body,
                     raw_response)
        return False

    def dispatch(self, request_body):
        arguments = parse(request_body)
        if not self.verify(request_body):
            return False

        event_name = self.get_response_event_type(arguments)
        if not event_name:
            return False

        response = self.get_response_instance(event_name,
                                              request_body,
                                              arguments)

        if not response:
            return False

        self.trigger(event_name, response)
        return True

    @staticmethod
    def get_response_instance(event_name, request_body, arguments):
        module_name = MODULE_MAPPING.get(event_name, None)
        if not module_name:
            return None

        module_name = 'pypal.ipn.%s' % module_name
        module_response = __import__(module_name, None, None, ['Response'], 0)
        if not (module_response or hasattr(module_response, 'Response')):
            return None
        return module_response.Response(request_body, arguments)

    @staticmethod
    def get_response_event_type(response):
        transaction_type = response.get('transaction_type', None)
        if not transaction_type:
            return None

        if not util.is_iterable(transaction_type):
            return transaction_type

        length = len(transaction_type)
        if length == 1:
            return transaction_type[0]
        return transaction_type


class Response(Response):
    @property
    def is_sandbox_transaction(self):
        return bool(self.get('test_ipn', False))
