import multiprocessing.dummy
from typing import Dict

import requests
from bs4 import BeautifulSoup
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils.http import urlencode
from django.views.generic import FormView, ListView
from urllib.parse import quote

from replay_viewer.forms import SubmissionForm
from replay_viewer.log_parser import PlayerParser, LogParser, PokeParser
from replay_viewer.models import Replay, Team, Player
from replay_viewer.utils import normalize_str

URL_HEADER = 'https://replay.pokemonshowdown.com/'


def search_replays(player_name, tier, url_header=URL_HEADER):
    """
    Query the PS replay database for the saved replays of a given username (limit: last 10 pages' worth of replays).
    """
    base_url = f'{URL_HEADER}search?user={quote(player_name)}'
    with multiprocessing.dummy.Pool(10) as pool:
        pages = filter(None, pool.map(lambda i: requests.get(f'{base_url}&page={i}').text, range(1, 11)))
    page = BeautifulSoup('\n'.join(pages), features='html.parser')

    urls = (url.get('href').strip('/') for url in page.findAll('a') if url.get('data-target'))
    return [f'{url_header}{url}' for url in urls if '-' in url and url.split('-')[-2].split('/')[-1] == tier]


@transaction.atomic
def process_replays(form) -> int:
    urls = {
        *form.cleaned_data['urls'],
        *search_replays(form.cleaned_data['player_name'], form.cleaned_data['tier'])
    } - set(Replay.objects.values_list('url', flat=True))
    if not urls: return 1

    logs = [requests.get(F'{url}.log').text for url in urls]
    parsed_logs = [LogParser(log, parsers=(PlayerParser, PokeParser)).parse() for log in logs]

    replays = Replay.objects.bulk_create(
        Replay(
            url=url,
            log=log,
            data=data,
        ) for url, log, data in zip(urls, logs, parsed_logs)
    )

    for i in (1, 2):
        players = Player.objects.bulk_create(
            # TODO: raw name
            Player(
               name=normalize_str(replay.data[f'p{i}']['player']['name']),
               player_num=i,
               replay=replay
            ) for replay in replays
        )
        Team.objects.bulk_create(
            Team(
                data=player.replay.data[f'p{i}']['team'],
                player=player,
                replay=player.replay
            ) for player in players
        )

    # short-term: do processing here and store in database
    # mid-term: background worker does processing
    # long-term: submit to external API for processing
    return 1


def get_metadata(log) -> Dict:
    players = get_players(log)
    return {
        'player_1': players['p1']['name'],
        'player_2': players['p2']['name'],
    }


def get_players(log) -> Dict:
    return LogParser(log, parsers=(PlayerParser,)).parse()


def get_teams(log):
    #return PokeParser(log, parsers=())
    # FIXME: Seems slower
    # res = requests.get(F'{url}.json').json()
    # lines = (line for line in res['log'].splitlines() if line.startswith('|poke'))

    lines = (line for line in log.splitlines() if line.startswith('|poke'))

    # res = requests.get(F'{url}').text
    # lines = (line for line in res.splitlines() if line.startswith('|poke'))
    cache = {}
    for i, line in enumerate(lines):
        if i == 12: break
        _, key, player, poke, item = line.split('|')
        species, *gender = poke.split(',')
        cache.setdefault(player, []).append(species)
    return cache['p1'], cache['p2']


class IndexView(FormView):
    template_name = 'index.html'
    form_class = SubmissionForm

    form = None
    task_id = None

    def form_valid(self, form):
        # Create a new async task
        self.form = form
        self.task_id = process_replays(form)
        return super().form_valid(form)

    def get_success_url(self):
        base_url = reverse('results', kwargs={'id': self.task_id})
        params = {
            'player_name': self.form.cleaned_data['player_name'],
            'urls': self.form.cleaned_data['urls'],
            'alt_names': self.form.cleaned_data['alt_names']
        }
        return f'{base_url}?{urlencode(params, True)}'#?player_name={self.form.cleaned_data["player_name"]}'
        #return f'{base_url}?player_name={self.form.cleaned_data["player_name"]}'


class ResultsView(ListView):
    template_name = 'results.html'

    def get_queryset(self):
        player_names = (
            normalize_str(name)
            for name in self.request.GET.getlist('alt_names') + [self.request.GET['player_name']]
        )
        # TODO: should fetch from a task name: messaging queue
        return Team.objects.filter(
            Q(player__name__in=player_names) |
            Q(replay__url__in=self.request.GET.getlist('urls'))
        ).prefetch_related('replay', 'player')
