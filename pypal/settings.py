# -*- coding: utf-8 -*-
"""
"""

SANDBOX_3TOKEN_ENDPOINT = 'https://api-3t.sandbox.paypal.com/nvp'
SANDBOX_CERTIFICATE_ENDPOINT = 'https://api.sandbox.paypal.com/nvp'

PRODUCTION_3TOKEN_ENDPOINT = 'https://api-3t.paypal.com/nvp'
PRODUCTION_CERTIFICATE_ENDPOINT = 'https://api.paypal.com/nvp'

NVP_FORMAT = 'NV'
XML_FORMAT = 'XML'
JSON_FORMAT = 'JSON'

SUPPORTED_FORMATS = {JSON_FORMAT: True,
                     NVP_FORMAT: True}

DEFAULT_REQUEST_ENVELOPE = {'errorLanguage': 'en_US'}

class Config(object):
    """
    """
    def __init__(self,
                 api_username=None,
                 api_password=None,
                 api_signature=None,
                 application_id=None,
                 token_authentication=True,
                 in_sandbox=True,
                 api_format=JSON_FORMAT,
                 request_envelope=DEFAULT_REQUEST_ENVELOPE,
                 **kwargs):
        """
        """
        self.api_username = api_username
        self.api_password = api_password
        self.api_signature = api_signature
        self.application_id = application_id
        self.token_authentication = token_authentication
        self.in_sandbox = in_sandbox
        self.api_format = api_format
        self.request_envelope = request_envelope

        if kwargs:
            for k, v in kwargs.items():
                setattr(self, k, v)

    def get_format(self):
        return self.api_format

    def set_format(self, choice):
        choice = choice.upper()
        is_supported = SUPPORTED_FORMATS.get(choice, False)
        if not is_supported:
            raise ValueError('Unsupported API format chosen')
        self.api_format = choice

    format = property(get_format, set_format)

    def is_sandbox_mode(self):
        return getattr(self, 'in_sandbox', True)

    @property
    def endpoint(self):
        if self.is_sandbox_mode():
            if self.token_authentication:
                return SANDBOX_3TOKEN_ENDPOINT
            return SANDBOX_CERTIFICATE_ENDPOINT

        if self.token_authentication:
            return PRODUCTION_3TOKEN_ENDPOINT
        return PRODUCTION_CERTIFICATE_ENDPOINT
