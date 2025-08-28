from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.conf import settings
from re import compile
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


EXEMPT_URLS = [compile(settings.LOGIN_URL.lstrip('/'))]
if hasattr(settings, 'LOGIN_EXEMPT_URLS'):
    EXEMPT_URLS += [compile(expr) for expr in settings.LOGIN_EXEMPT_URLS]


class LoginRequiredMiddleware(MiddlewareMixin):
    """
    Middleware that requires a user to be authenticated to view any page other
    than LOGIN_URL. Exemptions to this requirement can optionally be specified
    in settings via a list of regular expressions in LOGIN_EXEMPT_URLS.

    For users that are logged in it also updates the User.last_seen field.
    And checks if user needs a password reset.
    """
    def process_request(self, request):
        assert hasattr(request, 'user'), """
        The Login Required middleware needs to be after AuthenticationMiddleware.
        Also make sure to include the template context_processor:
        'django.contrib.auth.context_processors.auth'."""
        if not request.user.is_authenticated:
            path = request.path_info.lstrip('/')
            if not any(m.match(path) for m in EXEMPT_URLS):
                return HttpResponseRedirect(settings.LOGIN_URL)
        else:
            # Check and update last_seen
            if request.user.last_seen is None or \
                    request.user.last_seen + timedelta(minutes=settings.LAST_SEEN_TIMEOUT) < timezone.now():
                request.user.last_seen = timezone.now()
                request.user.save()

            if settings.USE_FEIDE_LOGIN:
                from allauth.socialaccount.models import SocialAccount
                # Check if user is FEIDE user, if so no need to check for password reset
                if SocialAccount.objects.filter(user=request.user).count() > 0:
                    return

            path = request.path_info
            if request.user.need_password_reset \
                    and path != reverse('reset_password')\
                    and path != reverse('password_change_done')\
                    and path != reverse('logout'):
                messages.error(request, 'You have a temporary password, please set your own password and keep it secret.')
                return redirect('reset_password')
