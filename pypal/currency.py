# -*- coding: utf-8 -*-

# North America
US_DOLLAR = 'USD'
CANADIAN_DOLLAR = 'CAD'
MEXICAN_PESO = 'MXN'

# South America
BRAZILIAN_REAL = 'BRL'

# Europe
EURO = 'EUR'
CZECH_KORUNA = 'CZK'
DANISH_KRONE = 'DKK'
NORWEGIAN_KRONE = 'NOK'
SWEDISH_KRONA = 'SEK'
HUNGARIAN_FORINT = 'HUF'
POUND_STERLING = 'GBP'
SWISS_FRANC = 'CHF'
POLISH_ZLOTY = 'PLN'

# Asia
HONG_KONG_DOLLAR = 'HKD'
JAPANEASE_YEN = 'JPY'
ISRAELI_NEW_SHEQEL = 'ILS'
MALAYSIAN_RINGGIT = 'MYR'
SINGAPORE_DOLLAR = 'SGD'
TAIWAN_NEW_DOLLAR = 'TWD'
THAI_BAHT = 'THB'
PHILIPPINE_PESO = 'PHP'

# Oceania
AUSTRALIAN_DOLLAR = 'AUD'
NEW_ZEALAND_DOLLAR = 'NZD'

NATIONALLY_ONLY = frozenset([BRAZILIAN_REAL, MALAYSIAN_RINGGIT])

ALL_CODES = frozenset([US_DOLLAR,
                       CANADIAN_DOLLAR,
                       MEXICAN_PESO,
                       BRAZILIAN_REAL,
                       EURO,
                       CZECH_KORUNA,
                       DANISH_KRONE,
                       NORWEGIAN_KRONE,
                       SWEDISH_KRONA,
                       HUNGARIAN_FORINT,
                       POUND_STERLING,
                       SWISS_FRANC,
                       POLISH_ZLOTY,
                       HONG_KONG_DOLLAR,
                       JAPANEASE_YEN,
                       ISRAELI_NEW_SHEQEL,
                       MALAYSIAN_RINGGIT,
                       SINGAPORE_DOLLAR,
                       TAIWAN_NEW_DOLLAR,
                       THAI_BAHT,
                       PHILIPPINE_PESO,
                       AUSTRALIAN_DOLLAR,
                       NEW_ZEALAND_DOLLAR])

NAME_MAPPING = {
    US_DOLLAR: 'United States dollar',
    CANADIAN_DOLLAR: 'Canadian dollar',
    MEXICAN_PESO: 'Mexican Peso',
    BRAZILIAN_REAL: 'Brazilian Real',
    EURO: 'Euro',
    CZECH_KORUNA: 'Czech Koruna',
    DANISH_KRONE: 'Danish Krone',
    NORWEGIAN_KRONE: 'Norwegian Krone',
    SWEDISH_KRONA: 'Swedish Krona',
    HUNGARIAN_FORINT: 'Hungarian Forint',
    POUND_STERLING: 'British Pound',
    SWISS_FRANC: 'Swiss Franc',
    POLISH_ZLOTY: 'Polish Zloty',
    HONG_KONG_DOLLAR: 'Hong Kong Dollar',
    JAPANEASE_YEN: 'Japanease Yen',
    ISRAELI_NEW_SHEQEL: 'Israeli New Sheqel',
    MALAYSIAN_RINGGIT: 'Malaysian Ringgit',
    SINGAPORE_DOLLAR: 'Singapore Dollar',
    TAIWAN_NEW_DOLLAR: 'Taiwan New Dollar',
    THAI_BAHT: 'Thai Baht',
    PHILIPPINE_PESO: 'Philippine Peso',
    AUSTRALIAN_DOLLAR: 'Australian Dollar',
    NEW_ZEALAND_DOLLAR: 'New Zealand Dollar'
}

def is_valid_code(code):
    return (code in ALL_CODES)

def is_supported_internationally(code):
    return not (code in NATIONALLY_ONLY)

def get_name(code):
    return NAME_MAPPING[code.upper()]
