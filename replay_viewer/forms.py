from django import forms


class SubmissionForm(forms.Form):
    tier = forms.CharField()
    player_name = forms.CharField(required=False)
    urls = forms.CharField(widget=forms.Textarea, required=False)
    alt_names = forms.CharField(widget=forms.Textarea, required=False)  # Add more
    thread = forms.URLField(required=False)

    # Required: one of (player_name, tier), urls

    def clean_urls(self):
        return self.data['urls'].splitlines()

    def clean_alt_names(self):
        return self.data['alt_names'].splitlines()
