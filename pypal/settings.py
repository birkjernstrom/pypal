# -*- coding: utf-8 -*-
"""
"""

SANDBOX_3TOKEN_ENDPOINT = 'https://api-3t.sandbox.paypal.com/nvp'
SANDBOX_CERTIFICATE_ENDPOINT = 'https://api.sandbox.paypal.com/nvp'

PRODUCTION_3TOKEN_ENDPOINT = 'https://api-3t.paypal.com/nvp'
PRODUCTION_CERTIFICATE_ENDPOINT = 'https://api.paypal.com/nvp'

NVP_PROTOCOL = 'NV'
XML_PROTOCOL = 'XML'
JSON_PROTOCOL = 'JSON'

SUPPORTED_PROTOCOLS = {NVP_PROTOCOL: True,
                       XML_PROTOCOL: True,
                       JSON_PROTOCOL: True}

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
                 protocol=NVP_PROTOCOL,
                 **kwargs):
        """
        """
        self.api_username = api_username
        self.api_password = api_password
        self.api_signature = api_signature
        self.application_id = application_id
        self.token_authentication = token_authentication
        self.in_sandbox = in_sandbox

        self.protocol = protocol

        if kwargs:
            for k, v in kwargs.items():
                setattr(self, k, v)

    def get_protocol(self):
        return getattr(self, '_protocol', JSON_PROTOCOL)

    def set_protocol(self, choice):
        choice = choice.upper()
        is_supported = SUPPORTED_PROTOCOLS.get(choice, False)
        if not is_supported:
            raise ValueError('Unsupported protocol chosen')
        self._protocol = choice

    protocol = property(get_protocol, set_protocol)

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
