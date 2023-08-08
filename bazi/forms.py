from django import forms


class BirthTimeForm(forms.Form):
    year = forms.IntegerField(min_value=1, max_value=9999)
    month = forms.IntegerField(min_value=1, max_value=12)
    day = forms.IntegerField(min_value=1, max_value=31)
