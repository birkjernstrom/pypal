# -*- coding: utf-8 -*-

import json

TIME_FORMAT = '%a %b %d %H:%M:%S %Y'

def convert_timestamp_into_utc(timestamp):
    """Convert given PayPal timestamp into UTC.

    We utilize pytz here since Pacific Standard Time is the timezone
    used in PayPal timestamps. However, in case UTC timestamps are
    not required in your application this can be disabled in your
    configuration, i.e no need to install pytz.

    :param timestamp: The PayPal timestamp
    """
    import time, pytz
    from datetime import datetime

    utc = pytz.timezone('UTC')
    paypal_timezone = pytz.timezone('US/Pacific')

    # This is a dragon. In the code. Hatching an egg.
    # This is in order to remove the timezone which cannot be
    # safely retrieved using %Z in the format string.
    # Since we use pytz we have also already explicitly
    # declared the timezone.
    timestamp = timestamp.split(' ')
    del timestamp[4]
    timestamp = ' '.join(timestamp)

    timestamp = time.mktime(time.strptime(timestamp, TIME_FORMAT))
    localized = paypal_timezone.localize(datetime.fromtimestamp(timestamp))
    normalized = paypal_timezone.normalize(localized)
    return normalized.astimezone(utc)

def check_required(arguments, required):
    for required_argument in required:
        v = arguments.get(required_argument, None)
        if v is None:
            raise ValueError('No value given for %s which is '
                             'a required argument' % required_argument)

def set_nonempty_param(params, key, value):
    if not value:
        return False
    params[key] = value
    return True

def is_iterable(obj):
    import collections
    return (isinstance(obj, collections.Iterable) and not
            isinstance(obj, basestring))

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
    return obj

def json_defaults(obj):
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    return obj
