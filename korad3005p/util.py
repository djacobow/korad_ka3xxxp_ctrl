
def flatten_dict(dd, separator='_', prefix=''):
    return {
        prefix + separator + k if prefix else k : v
            for kk, vv in dd.items()
                for k, v in flatten_dict(vv, separator, kk).items()
    } if isinstance(dd, dict) else {
        prefix : dd
    }

def listify_dict(data, labels_only=False):
    flat = flatten_dict(data)
    keys = sorted(flat.keys())
    if labels_only:
        return keys
    return [ flat[k] for k in keys ]

