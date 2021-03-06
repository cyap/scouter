import re
from typing import Dict


def normalize_str(s):
    """ Given a PS username, eliminate special characters and escaped unicode.

    Supported characters: Letters, numbers, spaces, period, apostrophe.
    """
    return re.sub("[^\w\s'\.-]+", "", re.sub("&#.*;", "", s)).lower().strip()


def recursive_update(source: Dict, patch: Dict):
    for k, v in patch.items():
        if type(source.get(k)) == dict:
            recursive_update(source[k], v)
        elif type(source.get(k)) == list:
            source[k] += v
        else:
            source[k] = v
