# -*- coding: utf-8 -*-


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


def prepare_nvp_dict(source, target={}, prefix=''):
    if not is_iterable(source):
        target[prefix] = source
        return target

    if isinstance(source, (list, tuple, set, frozenset)):
        index = 0
        for inner_value in source:
            inner_prefix = '%s(%s)' % (prefix, index)
            target = prepare_nvp_dict(inner_value, target, inner_prefix)
            index += 1
        return target

    for key, value in source.items():
        inner_prefix = key
        if prefix:
            inner_prefix = '%s.%s' % (prefix, key)
        target = prepare_nvp_dict(value, target, inner_prefix)
    return target
