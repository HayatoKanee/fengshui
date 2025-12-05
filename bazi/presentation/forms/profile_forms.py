"""
User Profile Forms.

Forms for creating and editing user BaZi profiles.
"""
from django import forms

from bazi.models import UserProfile


class UserProfileForm(forms.ModelForm):
    """
    User profile form for birth data input.

    Used to create and edit BaZi profiles with birth information
    including date, time, and gender.
    """

    class Meta:
        model = UserProfile
        fields = (
            "name",
            "birth_year",
            "birth_month",
            "birth_day",
            "birth_hour",
            "birth_minute",
            "is_male",
        )
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "birth_year": forms.NumberInput(
                attrs={"class": "form-control", "min": 0}
            ),
            "birth_month": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 12}
            ),
            "birth_day": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 31}
            ),
            "birth_hour": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "max": 23}
            ),
            "birth_minute": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "max": 59}
            ),
            "is_male": forms.RadioSelect(choices=[(True, "男"), (False, "女")]),
        }
