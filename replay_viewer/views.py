from typing import Dict, Iterable

import requests
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q, Prefetch
from django.http import HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic import FormView, ListView

from replay_viewer.forms import SubmissionForm, ScoutSerializationForm
from replay_viewer.log_parser import PlayerParser, LogParser, PokeParser
from replay_viewer.models import Replay, Team, Player, Scout
from replay_viewer.scrape import search_replays
from replay_viewer.utils import normalize_str


@transaction.atomic
def process_replays(
    raw_urls: Iterable[str] = None,
    player_name=None,
    tier=None,
    refresh=False
) -> int:
    urls = {*raw_urls}
    if not refresh:
        urls -= set(Replay.objects.values_list('url', flat=True))
    if not urls: return 1
    logs = [requests.get(F'{url}.json').json()['log'] for url in urls]
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

    #
    # @transaction.atomic()
    def form_valid(self, form):
        self.request.session['form_data'] = form.cleaned_data
        return super().form_valid(form)
        # self.scout.data = form.cleaned_data
        #     self.scout.save()

    def get_success_url(self):
        return reverse('results')
        #return reverse('results', kwargs={'id': self.scout.pk})


class BaseResultsView(ListView):
    template_name = 'results.html'

    def get_form_data(self):
        raise NotImplemented

    def get_queryset(self):
        form_data = self.get_form_data()
        serialization = form_data['serialization']
        player_name = normalize_str(form_data['player_name'])
        tier = form_data['tier']
        urls = {
            *form_data['urls'], *(replay['url'] for replay in serialization),
            *search_replays(player_name, tier)
        }
        process_replays(urls)

        # TODO: go back further
        teams = Team.objects.annotate(
            playerarr=ArrayAgg('replay__player__name')
        ).filter(
            Q(replay__url__in=urls),
            (Q(player__name__in=[player_name]) | ~Q(playerarr__contains=[player_name]))
        ).prefetch_related(
            Prefetch('replay', queryset=Replay.objects.prefetch_related('player_set')),
            'player'
        )

        # TODO: add additional teams from serialization
        ordering = {replay['url']: replay['team'] for replay in serialization}
        for team in teams:
            if team.replay.url in ordering:
                team.data.sort(
                    key=lambda x: next((i for i, pokemon in enumerate(ordering[team.replay.url]) if pokemon == x), 7)
                )
        return teams


class ResultsView(BaseResultsView):

    def get_form_data(self):
        try:
            return self.request.session['form_data']
        except KeyError:
            raise HttpResponseBadRequest


class ResultsShareView(BaseResultsView):

    def get_form_data(self):
        try:
            return {
                'serialization': Scout.objects.get(pk=self.kwargs['id']).data,
                'urls': [],
                'player_name': '',
                'tier': ''
            }
        except ObjectDoesNotExist:
            raise HttpResponseBadRequest


class ResultsSaveView(FormView):
    form_class = ScoutSerializationForm

    @staticmethod
    def _get_url(_id):
        return reverse('results_share', kwargs={'id': _id})

    @transaction.atomic
    def form_valid(self, form):
        scout = (
            Scout.objects.create(
                data=form.cleaned_data['serialization'],
                session_key=self.request.session.session_key
            )
            if form.cleaned_data['scout_id'] is None
            else Scout.objects.get(pk=form.cleaned_data['scout_id'])
        )
        return JsonResponse(data={
            'url': self._get_url(scout.pk),
            'scout_id': scout.pk
        })
