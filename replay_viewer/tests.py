import pytest
from django.test import TestCase

from replay_viewer.log_parser import LogParser, PlayerParser, PokeParser
from replay_viewer.utils import recursive_update


@pytest.mark.parametrize('base, target, expected', (
    (
        {},
        {},
        {}
    ),
    (
        {},
        {'p1': {'name': 'Eo'}},
        {'p1': {'name': 'Eo'}}
    ),
    (
        {'p1': {'name': 'Eo'}},
        {},
        {'p1': {'name': 'Eo'}}
    ),
    (
        {'p1': {'name': 'Eo'}},
        {'p2': {'name': 'hsa'}},
        {'p1': {'name': 'Eo'}, 'p2': {'name': 'hsa'}}
    ),
    (
        {'p1': {'name': 'Eo'}},
        {'p1': {'name': 'eo'}},
        {'p1': {'name': 'eo'}}
    ),
    (
        {'p1': {'name': 'Eo'}},
        {'p1': {'rating': 1800}},
        {'p1': {'name': 'Eo', 'rating': 1800}}
    ),
))
def test_recursive_update_dict(base, target, expected):
    recursive_update(base, target)
    assert base == expected


@pytest.mark.parametrize('base, target, expected', (
    (
        {'team': []},
        {'team': ['Clefable']},
        {'team': ['Clefable']}
    ),
    (
        {'team': ['Sylveon']},
        {'team': ['Clefable']},
        {'team': ['Sylveon', 'Clefable']}
    )
))
def test_recursive_update_list(base, target, expected):
    recursive_update(base, target)
    assert base == expected


# Parser tests

@pytest.mark.parametrize('log, expected', (
    (
        '|player|p1|Eo|#eo|\n|player|p2|hsa|wallace-gen3|',
        {
            'p1': {'player': {'name': 'Eo', 'avatar': '#eo'}},
            'p2': {'player': {'name': 'hsa', 'avatar': 'wallace-gen3'}}
        }
    ),
    # |player rejoins a match
    (
        '|player|p1|Eo|#eo|\n|player|p2|hsa|wallace-gen3|\n|player|p1|Eo',
        {
            'p1': {'player': {'name': 'Eo', 'avatar': '#eo'}},
            'p2': {'player': {'name': 'hsa', 'avatar': 'wallace-gen3'}}
        }
    ),
))
def test_player_parser(log, expected):
    assert LogParser(log=log, parsers=(PlayerParser,)).parse() == expected


@pytest.mark.parametrize('log, expected', (
    (
        '\n'.join(f'|poke|p{i}|{mon}|' for i, mon in (
            (1, 'Clefable, M'),
            (1, 'Sylveon, F'),
            (1, 'Ditto'),
            (2, 'Dragapult, M'),
            (2, 'Corviknight, F')
        )),
        {
            'p1': {'team': ['Clefable', 'Sylveon', 'Ditto']},
            'p2': {'team': ['Dragapult', 'Corviknight']}
        }
    ),
))
def test_poke_parser(log, expected):
    assert LogParser(log=log, parsers=(PokeParser,)).parse() == expected

