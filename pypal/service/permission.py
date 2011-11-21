# -*- coding: utf-8 -*-
"""
"""

import logging

PRODUCTION_ENDPOINT = 'https://svcs.paypal.com'
SANDBOX_ENDPOINT = 'https://svcs.sandbox.paypal.com'

REQUEST_TOKEN_TTL = 900

EXPRESS_CHECKOUT = 'EXPRESS_CHECKOUT'
DIRECT_PAYMENT = 'DIRECT_PAYMENT'
SETTLEMENT_CONSOLIDATION = 'SETTLEMENT_CONSOLIDATION'
SETTLEMENT_REPORTING = 'SETTLEMENT_REPORTING'
AUTH_CAPTURE = 'AUTH_CAPTURE'
MOBILE_CHECKOUT = 'MOBILE_CHECKOUT'
BILLING_AGREEMENT = 'BILLING_AGREEMENT'
REFERENCE_TRANSACTION = 'REFERENCE_TRANSACTION'
AIR_TRAVEL = 'AIR_TRAVEL'
MASS_PAY = 'MASS_PAY'
TRANSACTION_DETAILS = 'TRANSACTION_DETAILS'
TRANSACTION_SEARCH = 'TRANSACTION_SEARCH'
RECURRING_PAYMENTS = 'RECURRING_PAYMENTS'
ACCOUNT_BALANCE = 'ACCOUNT_BALANCE'
ENCRYPTED_WEBSITE_PAYMENTS = 'ENCRYPTED_WEBSITE_PAYMENTS'
REFUND = 'REFUND'
NON_REFERENCED_CREDIT = 'NON_REFERENCED_CREDIT'
BUTTON_MANAGER = 'BUTTON_MANAGER'
MANAGE_PENDING_TRANSACTION_STATUS = 'MANAGE_PENDING_TRANSACTION_STATUS'
RECURRING_PAYMENT_REPORT = 'RECURRING_PAYMENT_REPORT'
EXTENDED_PRO_PROCESSING_REPORT = 'EXTENDED_PRO_PROCESSING_REPORT'
EXCEPTION_PROCESSING_REPORT = 'EXCEPTION_PROCESSING_REPORT'
ACCOUNT_MANAGEMENT_PERMISSION = 'ACCOUNT_MANAGEMENT_PERMISSION'
ACCESS_BASIC_PERSONAL_DATA = 'ACCESS_BASIC_PERSONAL_DATA'
ACCESS_ADVANCED_PERSONAL_DATA = 'ACCESS_ADVANCED_PERSONAL_DATA'

REQUIRES_APPROVAL = frozenset([SETTLEMENT_CONSOLIDATION,
                               SETTLEMENT_REPORTING,
                               BILLING_AGREEMENT,
                               REFERENCE_TRANSACTION,
                               MASS_PAY,
                               TRANSACTION_DETAILS,
                               ACCOUNT_BALANCE,
                               ENCRYPTED_WEBSITE_PAYMENTS,
                               NON_REFERENCED_CREDIT])

REQUEST_PERMISSION_MAPPING = {
    # Express checkout mappings
    'SetExpressCheckout': EXPRESS_CHECKOUT,
    'GetExpressCheckout': EXPRESS_CHECKOUT,
    'DoExpressCheckout': EXPRESS_CHECKOUT,
    'GetPalDetails': EXPRESS_CHECKOUT,

    # Direct payment mappings
    'DoDirectPayment': DIRECT_PAYMENT,

    # Auth capture mappings
    'DoAuthorization': AUTH_CAPTURE,
    'DoCapture': AUTH_CAPTURE,
    'DoReauthorization': AUTH_CAPTURE,
    'DoVoid': AUTH_CAPTURE,

    # Mobile checkout mappings
    'SetMobileCheckout': MOBILE_CHECKOUT,
    'DoMobileCheckoutPayment': MOBILE_CHECKOUT,
    'CreateMobilePayment': MOBILE_CHECKOUT,

    # Billing agreement mappings
    'SetCustomerBillingAgreement': BILLING_AGREEMENT,
    'CreateBillingAgreement': BILLING_AGREEMENT,
    'BillAgreementUpdate': BILLING_AGREEMENT,
    'GetBillingAgreementCustomerDetails': BILLING_AGREEMENT,

    # Reference transaction mappings
    'DoReferenceTransaction': REFERENCE_TRANSACTION,

    # Air travel mappings
    'DoUATPAuthorization': AIR_TRAVEL,
    'DoUATPExpressCheckoutPayment': AIR_TRAVEL,

    # Mass pay mappings
    'MassPay': MASS_PAY,

    # Transaction details mappings
    'GetTransactionDetails': TRANSACTION_DETAILS,

    # Transaction search mappings
    'TransactionSearch': TRANSACTION_SEARCH,

    # Recurring payment mappings
    'CreateRecurringPaymentsProfile': RECURRING_PAYMENTS,
    'GetRecurringPaymentsProfileDetails': RECURRING_PAYMENTS,
    'ManageRecurringPaymentsProfileStatus': RECURRING_PAYMENTS,
    'UpdateRecurringPaymentsProfile': RECURRING_PAYMENTS,
    'BillOutstandingAmount': RECURRING_PAYMENTS,

    # Account balance mappings
    'GetBalance': ACCOUNT_BALANCE,

    # Refund mappings
    'RefundTransaction': REFUND,
    'Refund': REFUND,

    #: Non referenced credit mappings
    'DoNonReferencedCredit': NON_REFERENCED_CREDIT,

    #: Button manager mappings
    'BMManageButtonStatus': BUTTON_MANAGER,
    'BMCreateButton': BUTTON_MANAGER,
    'BMUpdateButton': BUTTON_MANAGER,
    'BMSetInventory': BUTTON_MANAGER,
    'BMGetInventory': BUTTON_MANAGER,
    'BMButtonSearch': BUTTON_MANAGER,

    # Manage pending transaction status mappings
    'ManagePendingTransactionStatus': MANAGE_PENDING_TRANSACTION_STATUS,

    # Retrieve personal data about an account which has granted
    # your application certain permissions.
    'GetBasicPersonalData': ACCESS_BASIC_PERSONAL_DATA,
    'GetAdvancedPersonalData': ACCESS_ADVANCED_PERSONAL_DATA
}


##############################################################################
# FUNCTIONS WHICH FURTHER AIDS IMPLEMENTATION OF THIS SERVICE
##############################################################################

def call(client, method, params):
    endpoint = (PRODUCTION_ENDPOINT, SANDBOX_ENDPOINT)
    endpoint = endpoint[int(client.config.in_sandbox)]
    return client.call('Permissions', method, endpoint=endpoint, **params)


def is_approval_required(group):
    return (group in REQUIRES_APPROVAL)


def is_operation_approval_required(operation):
    group = get_corresponding_group(operation)
    return is_approval_required(group)


def get_corresponding_group(operation):
    return REQUEST_PERMISSION_MAPPING.get(operation)


def get_grant_url(client, groups, callback_url):
    response = request(client, groups, callback_url)
    if not response.success:
        return None

    request_token = response.get('token', None)
    if not request_token:
        return None
    return client.get_paypal_url('/cgi-bin/webscr?cmd=_grant-permission'
                                 '&request_token=%s' % request_token)


def get_credentials(client, request_token, verification_code):
    response = get_access_token(client, request_token, verification_code)
    if not response.success:
        return (None, None)

    access_token = response.get('token', None)
    secret_token = response.get('tokenSecret', None)
    if access_token and secret_token:
        return (access_token, secret_token)
    return (None, None)

##############################################################################
# FUNCTIONS WHICH DIRECTLY CORRESPONDS TO PAYPAL API CALLS
##############################################################################

def get_access_token(client, request_token, verification_code):
    if not (request_token or verification_code):
        raise ValueError('Invalid arguments given')

    params = dict(token=request_token, verifier=verification_code)
    return call(client, 'GetAccessToken', params)


def get(client, access_token):
    return call(client, 'GetPermissions', dict(token=access_token))


def request(client, groups, callback_url):
    if not groups:
        raise ValueError('No groups given and therefore no request to'
                         'grant them is necessary')

    if not callback_url:
        raise ValueError('No callback URL specified; aborting request')

    params = dict(scope=groups, callback=callback_url)
    return call(client, 'RequestPermissions', params)


def cancel(client, access_token):
    return call(client, 'CancelPermissions', dict(token=access_token))
