from django import forms


class SubmissionForm(forms.Form):
    player_name = forms.CharField(required=False)
    tier = forms.CharField()
    urls = forms.CharField(widget=forms.Textarea, required=False)
    thread = forms.URLField(required=False)
    alt_names = forms.CharField(widget=forms.Textarea, required=False)  # Add more
    # TODO: validation
