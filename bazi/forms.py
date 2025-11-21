from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class BirthTimeForm(forms.Form):
    year = forms.IntegerField(min_value=0, label="出生年", required=True,
                              widget=forms.NumberInput(attrs={'class': 'form-control'}))
    month = forms.IntegerField(min_value=1, max_value=12, label="出生月", required=True,
                               widget=forms.NumberInput(attrs={'class': 'form-control'}))
    day = forms.IntegerField(min_value=1, max_value=31, label="出生日", required=True,
                             widget=forms.NumberInput(attrs={'class': 'form-control'}))
    hour = forms.IntegerField(min_value=0, max_value=23, label="出生时", required=True,
                              widget=forms.NumberInput(attrs={'class': 'form-control'}))
    minute = forms.IntegerField(min_value=0, max_value=59, label="出生分", required=False,
                                widget=forms.NumberInput(attrs={'class': 'form-control'}))
    gender = forms.ChoiceField(choices=[("male", "男"), ("female", "女")], label="性别", required=True,
                               widget=forms.RadioSelect(attrs={'class': 'form-check-input'}))


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('name', 'birth_year', 'birth_month', 'birth_day', 'birth_hour', 'birth_minute', 'is_male')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'birth_month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'birth_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 31}),
            'birth_hour': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 23}),
            'birth_minute': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 59}),
            'is_male': forms.RadioSelect(choices=[(True, "男"), (False, "女")])
        }
