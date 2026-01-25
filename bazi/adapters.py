"""
Custom allauth adapters for frictionless user experience.

Maintains the existing auto-registration behavior where:
- New usernames automatically create accounts
- Social logins auto-link to existing accounts by email
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter to maintain frictionless registration.
    """

    def is_open_for_signup(self, request):
        """Always allow signup."""
        return True

    def save_user(self, request, user, form, commit=True):
        """
        Save user with minimal required fields.
        Email is optional for frictionless UX.
        """
        user = super().save_user(request, user, form, commit=False)
        if commit:
            user.save()
        return user


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social adapter to handle account linking.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Auto-connect social account to existing user if email matches.
        Enables seamless social login for existing username/password users.
        """
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email')
        if email:
            try:
                user = User.objects.get(email__iexact=email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

    def is_open_for_signup(self, request, sociallogin):
        """Always allow social signup."""
        return True
