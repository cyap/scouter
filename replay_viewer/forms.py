import json
from collections import Iterable
from typing import Dict

from django import forms


class SubmissionForm(forms.Form):
    tier = forms.CharField()
    player_name = forms.CharField(required=False)
    urls = forms.CharField(widget=forms.Textarea, required=False)
    alt_names = forms.CharField(widget=forms.Textarea, required=False)  # Add more
    thread = forms.URLField(required=False)
    serialization = forms.CharField(widget=forms.Textarea, required=False)

    # Required: one of (player_name, tier), urls

    def clean_urls(self):
        return self.data['urls'].splitlines()

    def clean_alt_names(self):
        return self.data['alt_names'].splitlines()

    def clean_serialization(self):
        """
        Should be in the form:
        {"0":
            {'url': <str>, 'team' (optional): (...)
        }
        """
        if not self.data['serialization']: return []
        serialization = json.loads(self.data['serialization'])
        assert isinstance(serialization, Iterable), 'Is a list'
        assert all(isinstance(replay, Dict) for replay in serialization)
        assert all('url' in replay for replay in serialization)
        assert all(isinstance(replay.get('team', []), Iterable) for replay in serialization)
        return self.data['serialization']
