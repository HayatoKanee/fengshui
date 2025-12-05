"""
BaZi Analysis Forms.

Forms for birth time input used in BaZi calculations.
"""
from django import forms


class BirthTimeForm(forms.Form):
    """
    Birth time input form for BaZi analysis.

    Collects birth year, month, day, hour, minute, and gender
    for calculating the Four Pillars (BaZi).
    """

    year = forms.IntegerField(
        min_value=0,
        label="出生年",
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    month = forms.IntegerField(
        min_value=1,
        max_value=12,
        label="出生月",
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    day = forms.IntegerField(
        min_value=1,
        max_value=31,
        label="出生日",
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    hour = forms.IntegerField(
        min_value=0,
        max_value=23,
        label="出生时",
        required=True,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    minute = forms.IntegerField(
        min_value=0,
        max_value=59,
        label="出生分",
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    gender = forms.ChoiceField(
        choices=[("male", "男"), ("female", "女")],
        label="性别",
        required=True,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
