"""
REST API Views for Profile Management.

Provides JSON endpoints for the frontend to interact with profiles.
Used by authenticated users (local storage syncs to this on login).
"""
import json
from functools import wraps

from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from bazi.domain.models import BirthData
from bazi.domain.ports import ProfileData
from bazi.presentation.views.base import ContainerMixin


def login_required_json(view_func):
    """Decorator that returns JSON 401 for unauthenticated requests."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication required'},
                status=401
            )
        return view_func(request, *args, **kwargs)
    return wrapper


def profile_to_dict(profile: ProfileData) -> dict:
    """Convert ProfileData to JSON-serializable dict."""
    return {
        'id': profile.id,
        'name': profile.name,
        'birth_year': profile.birth_data.year,
        'birth_month': profile.birth_data.month,
        'birth_day': profile.birth_data.day,
        'birth_hour': profile.birth_data.hour,
        'birth_minute': profile.birth_data.minute,
        'is_male': profile.birth_data.is_male,
        'is_default': profile.is_default,
    }


@method_decorator(csrf_exempt, name='dispatch')
class ProfileAPIView(ContainerMixin, View):
    """
    API endpoint for listing and creating profiles.

    GET /api/profiles/ - List all profiles for the authenticated user
    POST /api/profiles/ - Create a new profile
    """

    @method_decorator(login_required_json)
    def get(self, request):
        """List all profiles for the current user."""
        profiles = self.profile_repo.get_by_user(request.user.id)
        return JsonResponse({
            'profiles': [profile_to_dict(p) for p in profiles]
        })

    @method_decorator(login_required_json)
    def post(self, request):
        """Create a new profile."""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Validate required fields
        required = ['name', 'birth_year', 'birth_month', 'birth_day', 'birth_hour']
        for field in required:
            if field not in data:
                return JsonResponse({'error': f'Missing field: {field}'}, status=400)

        # Create BirthData
        birth_data = BirthData(
            year=data['birth_year'],
            month=data['birth_month'],
            day=data['birth_day'],
            hour=data['birth_hour'],
            minute=data.get('birth_minute', 0),
            is_male=data.get('is_male', True),
        )

        # Check if this is the first profile (set as default)
        is_first = self.profile_repo.count_for_user(request.user.id) == 0

        # Create ProfileData
        profile_data = ProfileData(
            id=None,
            user_id=request.user.id,
            name=data['name'],
            birth_data=birth_data,
            is_default=is_first,
        )

        # Save via repository
        saved_profile = self.profile_repo.save(profile_data)

        return JsonResponse({
            'profile': profile_to_dict(saved_profile)
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class ProfileBatchAPIView(ContainerMixin, View):
    """
    API endpoint for batch creating profiles (migration from local storage).

    POST /api/profiles/batch/ - Create multiple profiles at once
    """

    @method_decorator(login_required_json)
    def post(self, request):
        """Batch create profiles from local storage migration."""
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        profiles_data = data.get('profiles', [])
        if not profiles_data:
            return JsonResponse({'error': 'No profiles provided'}, status=400)

        created_profiles = []
        existing_count = self.profile_repo.count_for_user(request.user.id)

        for i, p in enumerate(profiles_data):
            # Validate required fields
            required = ['name', 'birth_year', 'birth_month', 'birth_day', 'birth_hour']
            if not all(field in p for field in required):
                continue  # Skip invalid profiles silently

            birth_data = BirthData(
                year=p['birth_year'],
                month=p['birth_month'],
                day=p['birth_day'],
                hour=p['birth_hour'],
                minute=p.get('birth_minute', 0),
                is_male=p.get('is_male', True),
            )

            # First migrated profile becomes default if no existing profiles
            is_default = (existing_count == 0 and i == 0)

            profile_data = ProfileData(
                id=None,
                user_id=request.user.id,
                name=p['name'],
                birth_data=birth_data,
                is_default=is_default,
            )

            saved = self.profile_repo.save(profile_data)
            created_profiles.append(saved)

        return JsonResponse({
            'created': len(created_profiles),
            'profiles': [profile_to_dict(p) for p in created_profiles]
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class ProfileDetailAPIView(ContainerMixin, View):
    """
    API endpoint for single profile operations.

    GET /api/profiles/<id>/ - Get a single profile
    PATCH /api/profiles/<id>/ - Update a profile
    DELETE /api/profiles/<id>/ - Delete a profile
    """

    def get_profile_or_error(self, request, profile_id):
        """Get profile ensuring it belongs to current user."""
        profile = self.profile_repo.get_by_id(profile_id)
        if not profile or profile.user_id != request.user.id:
            return None, JsonResponse({'error': 'Profile not found'}, status=404)
        return profile, None

    @method_decorator(login_required_json)
    def get(self, request, profile_id):
        """Get a single profile."""
        profile, error = self.get_profile_or_error(request, profile_id)
        if error:
            return error
        return JsonResponse({'profile': profile_to_dict(profile)})

    @method_decorator(login_required_json)
    def patch(self, request, profile_id):
        """Update a profile."""
        profile, error = self.get_profile_or_error(request, profile_id)
        if error:
            return error

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Build updated BirthData
        birth_data = BirthData(
            year=data.get('birth_year', profile.birth_data.year),
            month=data.get('birth_month', profile.birth_data.month),
            day=data.get('birth_day', profile.birth_data.day),
            hour=data.get('birth_hour', profile.birth_data.hour),
            minute=data.get('birth_minute', profile.birth_data.minute),
            is_male=data.get('is_male', profile.birth_data.is_male),
        )

        updated_profile = ProfileData(
            id=profile_id,
            user_id=request.user.id,
            name=data.get('name', profile.name),
            birth_data=birth_data,
            is_default=profile.is_default,
        )

        saved = self.profile_repo.save(updated_profile)
        return JsonResponse({'profile': profile_to_dict(saved)})

    @method_decorator(login_required_json)
    def delete(self, request, profile_id):
        """Delete a profile."""
        profile, error = self.get_profile_or_error(request, profile_id)
        if error:
            return error

        self.profile_repo.delete(profile_id)
        return JsonResponse({'success': True})


@method_decorator(csrf_exempt, name='dispatch')
class ProfileDefaultAPIView(ContainerMixin, View):
    """
    API endpoint for setting the default profile.

    POST /api/profiles/<id>/default/ - Set profile as default
    """

    @method_decorator(login_required_json)
    def post(self, request, profile_id):
        """Set a profile as default."""
        profile = self.profile_repo.get_by_id(profile_id)
        if not profile or profile.user_id != request.user.id:
            return JsonResponse({'error': 'Profile not found'}, status=404)

        self.profile_repo.set_default(profile_id, request.user.id)

        # Return updated profile
        updated = self.profile_repo.get_by_id(profile_id)
        return JsonResponse({'profile': profile_to_dict(updated)})


# URL-compatible view instances
profile_api = ProfileAPIView.as_view()
profile_batch_api = ProfileBatchAPIView.as_view()
profile_detail_api = ProfileDetailAPIView.as_view()
profile_default_api = ProfileDefaultAPIView.as_view()
