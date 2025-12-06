"""
User Profile Forms.

Forms for creating and editing user BaZi profiles.
DIP-compliant: Uses regular Form instead of ModelForm to avoid Django model coupling.
"""
from django import forms


class UserProfileForm(forms.Form):
    """
    User profile form for birth data input.

    Used to create and edit BaZi profiles with birth information
    including date, time, and gender.

    This is a regular Form (not ModelForm) to maintain DIP compliance.
    The view layer handles conversion to ProfileData domain objects.
    """

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="名称",
    )
    birth_year = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        label="出生年",
    )
    birth_month = forms.IntegerField(
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 12}),
        label="出生月",
    )
    birth_day = forms.IntegerField(
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 31}),
        label="出生日",
    )
    birth_hour = forms.IntegerField(
        min_value=0,
        max_value=23,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 23}),
        label="出生时",
    )
    birth_minute = forms.IntegerField(
        min_value=0,
        max_value=59,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 59}),
        label="出生分",
    )
    is_male = forms.TypedChoiceField(
        choices=[(True, "男"), (False, "女")],
        coerce=lambda x: x == "True" or x is True,
        widget=forms.RadioSelect(),
        initial=True,
        label="性别",
    )
