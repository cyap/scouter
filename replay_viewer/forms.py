import json
from collections import Iterable
from typing import Dict

from django import forms
from django.core.exceptions import ValidationError


class SerializationFormMixin:
    def clean_serialization(self):
        ERROR_MSG = """Serialization should be in the following form:
        [
            {
                "url": https://replay.pokemonshowdown.com/smogtours-ou-39893,
                "team":["Clefable","Hippowdon","Excadrill","Rotom-Mow","Mandibuzz","Dragapult"]
                "player": 1
            },
            {
                "url": ...
                "team": ...
                "player": ...
            },
            ...
        ]
        """
        if not self.data['serialization']:
            return []

        try:
            serialization = json.loads(self.data['serialization'])
            assert isinstance(serialization, Iterable)
            assert all(isinstance(replay, Dict) for replay in serialization)
            assert all(isinstance(replay.get('url'), str) for replay in serialization)
            assert all(isinstance(replay.get('player'), int) for replay in serialization)
            # assert all(isinstance(replay.get('team', []), Iterable) for replay in serialization)
        except (AssertionError, json.JSONDecodeError):
            raise ValidationError(ERROR_MSG)
        else:
            return serialization


class SubmissionForm(forms.Form):
    player_name = forms.CharField(required=False)
    tier = forms.CharField(required=False)
    urls = forms.CharField(widget=forms.Textarea, required=False)
    #thread = forms.URLField(required=False)
    # TODO: duplicate form fields

    # Required: one of (player_name, tier), urls

    def clean_urls(self):
        return self.data['urls'].splitlines()

    def clean(self):
        try:
            assert any((
                self.data['tier'] and self.data['player_name'],
                self.data['urls'],
                #self.data['thread'],
            ))
        except AssertionError:
            raise ValidationError('One of the following is required: tier/player_name, urls, serialization.')

        return super().clean()

    def as_serialization(self):
        urls = {replay['url'] for replay in self.cleaned_data['serialization']}
        return self.cleaned_data['serialization'] + [{
            'url': url,
            'team': None
        } for url in self.cleaned_data['urls'] if url not in urls]


class ScoutSerializationForm(forms.Form, SerializationFormMixin):
    serialization = forms.CharField(widget=forms.Textarea, required=False)
    scout_id = forms.IntegerField(required=False)
