# -*- coding: utf-8 -*-

import logging

from pypal import currency
from pypal.util import check_required, set_nonempty_param

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
    """An extension of the native list type which ensures all contained items
    are dictionaries - containing the necessary arguments needed per receiver.

    """
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
    """A wrapper of the ``'pypal.Client.call'`` method which
    will set the API endpoints for this service depending
    on the environment, i.e sandbox or not.

    :param client: An instance of ``'pypal.Client'``
    :param method: The API method to execute
    :param params: The arguments to send
    """
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
    """Executes the Pay API call and returns the intended redirect URL
    directly using the necessary pay key returned in the PayPal response.

    This function is a wrapper of ``'pay'`` which will execute the necessary
    API calls and using the response this function will generate the URL.

    """
    response = pay(**locals())
    if not response.success:
        return None

    pay_key = response.get('payKey', None)
    if not pay_key:
        return None
    return generate_pay_url(client, pay_key)

def generate_pay_url(client, pay_key):
    """Retrieves the pay key associated with prepared payment procedures and
    generates the intended URL to redirect end-users in order to finialize
    payments.

    :param client: An instance of ``'pypal.Client'``
    :param pay_key: The payment token received from PayPal
    """
    return client.get_paypal_url('/cgi-bin/webscr?cmd=_ap-payment'
                                 '&paykey=%s' % pay_key)

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
        extra={}):
    """Execute the Pay API call which will prepare the payment procedure.
    Most importantly it will return a pay key which should be utilized in
    order to identify the transaction.

    :param client: An instance of ``'pypal.Client'``
    :param action_type: The payment action type
    :param currency_code: Which currency code to utilize in the transaction
    :param cancel_url: The URL which the end-user is sent to on
                       payment cancellation.
    :param return_url: The URL which the end-user is sent to on completed
                       payment, in all cases be it success or failure.
    :param ipn_callback_url: Override the IPN URL which PayPal will send
                             notifications to regarding this request.
    :param receivers: A list of the receivers of this transaction
    :param extra: Additional key-value arguments to send to PayPal
    """
    check_required(locals(), ('cancel_url', 'return_url', 'currency_code',
                              'action_type', 'receivers'))

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

    extra.update({'actionType': action_type,
                  'receiverList.receiver': receivers,
                  'currencyCode': currency_code,
                  'cancelUrl': cancel_url,
                  'returnUrl': return_url,
                  'requestEnvelope.errorLanguage': 'en_US'})

    if ipn_callback_url is not None:
        extra['ipnNotificationUrl'] = ipn_callback_url
    return call(client, 'Pay', extra)

def get_payment_options(client, pay_key):
    return call(client, 'GetPaymentOptions', {'payKey': pay_key})

def set_payment_options(client,
                        pay_key,
                        sender_options=None,
                        receiver_options=None,
                        display_options=None,
                        shipping_address_id=None,
                        initiating_entity=None,
                        extra={}):
    """Execute the SetPaymentOptions API call which will customize
    behavior of the payment procedure at PayPal.

    :param client: An instance of ``'pypal.Client'``
    :param pay_key: The PayPal token associated with the transaction
    :param sender_options: Dictionary containing sender customizations
    :param receiver_options: Dictionary containing receiver customizations
    :param display_options: Dictionary containing display customizations
    :param shipping_address_id: The PayPal identifier for the shipping
                                address to set.
    :param initiating_entity: Dictionary containing initiating entity
                              customizations.
    :param extra: Additional key-value arguments to send to PayPal
    """
    extra['payKey'] = pay_key
    set_nonempty_param(extra, 'initiatingEntity', initiating_entity)
    set_nonempty_param(extra, 'displayOptions', display_options)
    set_nonempty_param(extra, 'shippingAddressId', shipping_address_id)
    set_nonempty_param(extra, 'senderOptions', sender_options)
    set_nonempty_param(extra, 'receiverOptions', receiver_options)
    logging.debug(extra)
    return call(client, 'SetPaymentOptions', extra)

def get_shipping_addresses(client, key):
    """Execute the GetShippingAddresses API call which will retrieve
    the shipping address which was set by the buyer.

    :param token: Either a payment or preapproval key
    """
    return call(client, 'GetShippingAddresses', {'key': key})
