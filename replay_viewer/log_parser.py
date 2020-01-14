from typing import List, Union

from replay_viewer.utils import recursive_update


class LogParser:

    def __init__(self, log: str, parsers=None):
        self.lines = log.splitlines()
        self.parsers = parsers or []

        self.state = {}
        self.res = {}
        self.match_counts = {}

    def parse(self):
        for i, line in enumerate(self.lines):
            for parser in self.parsers:
                parser(line, i, self.res, self.state, self.match_counts).parse()
        return self.res


class BaseLineParser:

    def __init__(self, line, line_number, res, state, match_counts):
        self.line = line
        self.line_number = line_number

        self.res = res
        self.state = state
        self.match_counts = match_counts

    @property
    def parse_predicate(self) -> bool:
        """
            If line meets condition, parse it.
        """
        raise NotImplementedError

    def parse(self):
        raise NotImplementedError


class LineParser(BaseLineParser):
    # Assumes all lines are |key|blah

    @property
    def key(self) -> str:
        raise NotImplementedError

    @property
    def props(self) -> List[Union[str, None]]:
        raise NotImplementedError

    def update_res(self, data):
        raise NotImplementedError

    def update_state(self, data):
        raise NotImplementedError

    @property
    def parse_predicate(self):
        return self.line.startswith(self.key)

    def get_data(self):
        return {
            k: v for k, v in zip(self.props, self.line.split('|'))
            if k is not None
        }

    @property
    def match_count(self):
        return self.match_counts.get(self.__class__, 0)

    def parse(self):
        if not self.parse_predicate:
            return {}
        data = self.get_data()
        self.update_res(data)
        self.update_state(data)

        self.match_counts[self.__class__] = self.match_count + 1
        return self.res


class PlayerParser(LineParser):
    key = '|player'
    props = [None, None, 'player_key', 'name', 'avatar']

    @property
    def parse_predicate(self):
        return super().parse_predicate and self.match_count < 2

    def update_res(self, data):
        recursive_update(self.res, {
            data['player_key']: {
                'player': {
                    'name': data['name'],
                    'avatar': data['avatar'],
                }
            }
        })

    def update_state(self, data):
        pass  # NO-OP


class PokeParser(LineParser):
    key = '|poke'
    props = [None, None, 'player_key', 'pokemon', 'item']

    @property
    def parse_predicate(self):
        return super().parse_predicate and self.match_count < 12

    def update_res(self, data):
        species, *gender = data['pokemon'].split(',')
        recursive_update(self.res, {
            data['player_key']: {
               'team': [species]
            }
        })

    def update_state(self, data):
        pass  # NO-OP


# class Parser(BaseParser):

# @property
# def match_function(self):
#     return functools.partial(str.startswith, self.key)

#
# def get_teams(log):
#     # res = requests.get(F'{url}.json').json()
#     # lines = (line for line in res['log'].splitlines() if line.startswith('|poke'))
#
#     lines = (line for line in log.splitlines() if line.startswith('|poke'))
#
#     # res = requests.get(F'{url}').text
#     # lines = (line for line in res.splitlines() if line.startswith('|poke'))
#     cache = {}
#     for i, line in enumerate(lines):
#         if i == 12: break
#         _, key, player, poke, item = line.split('|')
#         species, *gender = poke.split(',')
#         cache.setdefault(player, []).append(species)
#     return cache['p1'], cache['p2']

