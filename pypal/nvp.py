# -*- coding: utf-8 -*-
"""
This module handles processing of the PayPal Name-Value Pair (NVP) format.
In essence it is similar to HTTP query strings. However, PayPal indicates
the hierarchical relationship between key-value pairs by formatting the keys
according to a special syntax.

Using this module both one level and nested dictionaries are supported and
encoded / decoded according to the PayPal standards.

For more information regarding this format read the PayPal NVP documentation::
    http://bit.ly/ssWiEH
"""
import logging

from urlparse import parse_qs
from urllib import urlencode

DO_LOG = False

#: The string which we should split all keys by in order to
#: retreive the hierarchical structure intended by PayPal.
KEY_HIERARCHY_INDICATOR = '.'

#: The needles to search for in order to detect values which
#: should be converted into a list. These strings are always
#: placed at the end of the key.
KEY_LIST_CLOSE_INDICATORS = frozenset([']', ')'])

#: Dictionary which maps the close and open indicators utilized
#: to contain the order integer of the intended list value.
KEY_LIST_INDICATOR_MAPPING = {']': '[',
                              ')': '('}

def log(message, *args):
    if not DO_LOG:
        return
    logging.debug(message, *args)

def parse(response):
    """Iterate through the one-level deep dictionary and construct another
    dictionary reflecting the hierarchical relationship between all key-values.

    The hierarchy is determined depending on whether key values consist of
    logical group names joined by ``'KEY_HIERARCHY_INDICATOR'``.

    An example is responseEnvelope.timestamp where timestamp is the key while
    responseEnvelope is the associated key group.

    In such instances the key is split by the same 

    :param response: Either the raw PayPal response or the dictionary retrieved
                     by previously parsing the response using the parse function.
    """
    if not isinstance(response, dict):
        response = parse_qs(response)

    dictionary = {}
    for k, v in response.items():
        hierarchy = k.split(KEY_HIERARCHY_INDICATOR)
        dictionary = _recursive_conversion(dictionary, hierarchy, v)
    return dictionary

def render(dictionary):
    log('%s: Pre-render: %s' % (id(dictionary), dictionary))
    dictionary = _prepare_hierarchical_rendering(dictionary)
    log('%s: Render: %s' % (id(dictionary), dictionary))
    generated = urlencode(dictionary)
    log('%s: Generated %s' % (id(dictionary), dictionary))
    return generated

def _prepare_hierarchical_rendering(source, target=[], prefix=''):
    if isinstance(source, (list, tuple, set, frozenset)):
        index = 0
        for inner_value in source:
            inner_prefix = '%s[%s]' % (prefix, index)
            target = _prepare_hierarchical_rendering(inner_value, target, inner_prefix)
            index += 1
        return target

    if not isinstance(source, dict):
        target.append((prefix, source))
        return target

    for key, value in source.items():
        inner_prefix = key
        if prefix:
            inner_prefix = '%s.%s' % (prefix, key)
        target = _prepare_hierarchical_rendering(value, target, inner_prefix)
    return target

def _recursive_conversion(dictionary, hierarchical_key, value):
    """Iterate through all logical parts of a hierarchical key list
    and update the given dictionary to reflect the found hierarchy.

    Also determine whether given value should be contained in a list
    rather than contained separately.

    :param dictionary: The dictionary to manipulate
    :param hierarchical_key: List containing all the logical parts found
                             in the key-value pair.
    :param value: The value which is associated with given key
    """
    if not hierarchical_key:
        if len(value) == 1:
            return value[0]
        return value

    root = hierarchical_key.pop(0)
    root, hierarchical_key = _parse_hierarchical_key(hierarchical_key, root)

    if root not in dictionary:
        dictionary[root] = {}

    dictionary[root] = _recursive_conversion(dictionary[root],
                                             hierarchical_key,
                                             value)
    return dictionary

def _parse_hierarchical_key(hierarchical_key, root_key):
    replaced = root_key
    if not isinstance(root_key, basestring):
        return (replaced, hierarchical_key)

    close_character = root_key[-1]
    if not close_character in KEY_LIST_CLOSE_INDICATORS:
        return (replaced, hierarchical_key)

    open_character = KEY_LIST_INDICATOR_MAPPING[close_character]
    try:
        # Find the first occurence of ``'open_character'`` and
        # construct the list necessary to contain all items associated
        # with that context, i.e having the same context identifier.
        offset = root_key.index(open_character)
        # Retrieve the order identifier (integer)
        hierarchical_order = int(root_key[(offset + 1):-1])
        # Remove hierarchical order identifier from the
        # root key - it should construct another level of
        # depth in the dictionary.
        replaced = root_key[:offset]
        # Insert the hierarchical order indicator in our
        # list of key components.
        hierarchical_key.insert(0, hierarchical_order)
    except ValueError:
        pass
    return (replaced, hierarchical_key)
