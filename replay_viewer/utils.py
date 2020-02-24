import re
from typing import Dict


def normalize_str(s):
    """ Given a PS username, eliminate special characters and escaped unicode.

    Supported characters: Letters, numbers, spaces, period, apostrophe.
    """
    return re.sub("[^\w\s'\.-]+", "", re.sub("&#.*;", "", s)).lower().strip()


def to_sprite(pokemon_name):
    return {
        'gastrodon-east': 'gastrodon',
        'gastrodon-west': 'gastrodon',
    }.get(pokemon_name, pokemon_name.replace(' ', '-'))


def recursive_update(source: Dict, patch: Dict):
    for k, v in patch.items():
        if type(source.get(k)) == dict:
            recursive_update(source[k], v)
        elif type(source.get(k)) == list:
            source[k] += v
        else:
            source[k] = v


def delete_duplicates(replays):
    cache = set()
    for replay in replays:
        if replay.url not in cache:
            cache.add(replay.url)
        else:
            replay.delete()
