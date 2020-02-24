import multiprocessing.dummy
from typing import Iterable
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

URL_HEADER = 'https://replay.pokemonshowdown.com/'
PAGE_START = 1
PAGE_END = 11


def search_replays(player_name, tier, url_header=URL_HEADER) -> Iterable[str]:
    """
    Query the PS replay database for the saved replays of a given username (limit: last 10 pages' worth of replays).
    """
    base_url = f'{URL_HEADER}search?user={quote(player_name)}'
    with multiprocessing.dummy.Pool(PAGE_END-PAGE_START) as pool:
        pages = filter(
            None,
            pool.map(lambda i: requests.get(f'{base_url}&page={i}').text, range(PAGE_START, PAGE_END))
        )
    page = BeautifulSoup('\n'.join(pages), features='html.parser')

    urls = (url.get('href').strip('/') for url in page.findAll('a') if url.get('data-target'))
    return [f'{url_header}{url}' for url in urls if '-' in url and url.split('-')[-2].split('/')[-1] == tier]
