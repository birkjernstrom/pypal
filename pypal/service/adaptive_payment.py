# -*- coding: utf-8 -*-

import logging

from pypal import currency

PRODUCTION_ENDPOINT = 'https://svcs.paypal.com'
SANDBOX_ENDPOINT = 'https://svcs.sandbox.paypal.com'

PAY_ACTION = 'PAY'
CREATE_ACTION = 'CREATE'
PAY_PRIMARY_ACTION = 'PAY_PRIMARY'

EXISTING_PAY_ACTIONS = frozenset([PAY_ACTION,
                                  CREATE_ACTION,
                                  PAY_PRIMARY_ACTION])

##############################################################################
# FUNCTIONS WHICH FURTHER AIDS IMPLEMENTATION OF THIS SERVICE
##############################################################################

class ReceiverList(list):
    def __init__(self, iterable):
        if iterable:
            self.extend(iterable)

    def append(self, obj):
        email = obj.get('email', None)
        amount = obj.get('amount', None)
        if email and amount:
            super(type(self), self).append(obj)
        return False

    def extend(self, iterable):
        for obj in iterable:
            self.append(obj)

def call(client, method, params):
    endpoint = (PRODUCTION_ENDPOINT, SANDBOX_ENDPOINT)
    endpoint = endpoint[int(client.config.in_sandbox)]
    return client.call('AdaptivePayments', method,
                       endpoint=endpoint, **params)

def get_pay_url(client,
                action_type,
                currency_code,
                cancel_url,
                return_url,
                ipn_callback_url=None,
                receivers=None):
    """
    """
    response = pay(**locals())
    if not response.success:
        return None

    token = response.get('payKey', None)
    if not token:
        return None
    return client.get_paypal_url('/cgi-bin/webscr?cmd=_ap-payment'
                                 '&paykey=%s' % token)



##############################################################################
# FUNCTIONS WHICH DIRECTLY CORRESPONDS TO PAYPAL API CALLS
##############################################################################

def pay(client,
        action_type,
        currency_code,
        cancel_url,
        return_url,
        ipn_callback_url=None,
        receivers=None,
        **kwargs):
    """
    """
    if not cancel_url:
        raise ValueError('Missing callback URL for the cancel action')

    if not return_url:
        raise ValueError('Missing callback URL for the return action')

    if not currency.is_valid_code(currency_code):
        raise ValueError('Given currency code (%s) '
                         'is not supported' % currency_code)

    if action_type not in EXISTING_PAY_ACTIONS:
        raise ValueError('Given payment action (%s) is not any of the '
                         'supported types; %s' % (action_type,
                                                  EXISTING_PAY_ACTIONS))

    if not isinstance(receivers, ReceiverList):
        if not isinstance(receivers, (list, tuple)):
            receivers = [receivers]
        receivers = ReceiverList(receivers)

    if not receivers:
        raise ValueError('No receivers given')

    params = {'actionType': action_type,
              'receiverList.receiver': receivers,
              'currencyCode': currency_code,
              'cancelUrl': cancel_url,
              'returnUrl': return_url,
              'requestEnvelope.errorLanguage': 'en_US'}

    if ipn_callback_url is not None:
        params['ipnNotificationUrl'] = ipn_callback_url

    params.update(kwargs)
    logging.debug(params)
    return call(client, 'Pay', params)
