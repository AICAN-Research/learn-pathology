from datetime import datetime
from allauth.socialaccount.helpers import render_authentication_error, complete_social_login
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.base import ProviderException, AuthAction, AuthError
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView, OAuth2View,
)
from allauth.utils import get_request_param
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from oauthlib.oauth2 import OAuth2Error
from requests import RequestException

from .models import ApprovedUser
from .provider import DataportenProvider, DataportenAdapter
import json

class FeideCallbackView(OAuth2CallbackView):
    """
    We override the OAuth2CallbackView to handle errors in authorization.
    """

    def dispatch(self, request, *args, **kwargs):
        if "error" in request.GET or "code" not in request.GET:
            # Distinguish cancel from error
            auth_error = request.GET.get("error", None)
            if auth_error == self.adapter.login_cancelled_error:
                error = AuthError.CANCELLED
            else:
                error = AuthError.UNKNOWN
            return render_authentication_error(
                request, self.adapter.provider_id, error=error
            )
        app = self.adapter.get_provider().app
        client = self.adapter.get_client(self.request, app)

        try:
            access_token = self.adapter.get_access_token_data(request, app, client)
            token = self.adapter.parse_token(access_token)
            if app.pk:
                token.app = app
            login = self.adapter.complete_login(
                request, app, token, response=access_token
            )
            login.token = token
            if self.adapter.supports_state:
                login.state = SocialLogin.verify_and_unstash_state(
                    request, get_request_param(request, "state")
                )
            else:
                login.state = SocialLogin.unstash_state(request)

            return complete_social_login(request, login)
        except (
            PermissionDenied,
            OAuth2Error,
            RequestException,
            ProviderException,
        ) as e:
            messages.add_message(request, messages.ERROR, str(e))
            return redirect('login_feide')


oauth2_login = OAuth2LoginView.adapter_view(DataportenAdapter)
oauth2_callback = FeideCallbackView.adapter_view(DataportenAdapter)
