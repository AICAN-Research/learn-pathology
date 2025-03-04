from datetime import datetime

from allauth.socialaccount.adapter import get_adapter
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
from .provider import DataportenProvider
import json


class DataportenAdapter(OAuth2Adapter):
    provider_id = DataportenProvider.id
    access_token_url = "https://auth.dataporten.no/oauth/token"
    authorize_url = "https://auth.dataporten.no/oauth/authorization"
    profile_url = "https://auth.dataporten.no/userinfo"
    groups_url = "https://groups-api.dataporten.no/groups/me/groups"
    extended_user_info = 'https://api.dataporten.no/userinfo/v1/userinfo'

    def complete_login(self, request, app, token, **kwargs):
        """
        Arguments:
            request - The get request to the callback URL
                        /accounts/dataporten/login/callback.
            app - The corresponding SocialApp model instance
            token - A token object with access token given in token.token
        Returns:
            Should return a dict with user information intended for parsing
            by the methods of the DataportenProvider view, i.e.
            extract_uid(), extract_extra_data(), and extract_common_fields()
        """
        # The authentication header
        headers = {"Authorization": "Bearer " + token.token}

        # Userinfo endpoint, for documentation see:
        # https://docs.dataporten.no/docs/oauth-authentication/
        userinfo_response = (
            get_adapter()
            .get_requests_session()
            .get(
                self.profile_url,
                headers=headers,
            )
        )
        # Raise exception for 4xx and 5xx response codes
        userinfo_response.raise_for_status()

        # Check that user belongs to NTNU and check whether person is on the approved user list
        ntnu_found = False
        approved_user = False
        for userid_sec in userinfo_response.json()['user']['userid_sec']:
            username = userid_sec.split(':')[1]
            org = username.split('@')[1]
            if org == 'ntnu.no':
                ntnu_found = True
                # Check if user is on the pre approved list
                try:
                    user = ApprovedUser.objects.get(username=username)
                    approved_user = True
                except ApprovedUser.DoesNotExist:
                    pass
        if not ntnu_found:
            raise ProviderException('Only NTNU users are allowed to login to LearnPathology.')

        #print(json.dumps(userinfo_response.json(), indent=2))
        userinfo2_response = (
            get_adapter()
                .get_requests_session()
                .get(
                self.extended_user_info,
                headers=headers,
            )
        )
        #print(json.dumps(userinfo2_response.json(), indent=2))

        # Get group info
        groupinfo_response = (
            get_adapter()
                .get_requests_session()
                .get(
                self.groups_url,
                headers=headers,
            )
        )

        # Check if user is enrolled in medical studies
        #print(json.dumps(groupinfo_response.json(), indent=2))
        ntnu_found = False
        medical_student = False
        student = False
        faculty = False
        #enrolled_in_relevant_course = False
        if not approved_user:
            for group in groupinfo_response.json():
                if group['id'] == 'fc:org:ntnu.no':
                    ntnu_found = True
                    if group['membership']['primaryAffiliation'] == 'faculty':
                        faculty = True
                    for aff in group['membership']['affiliation']:
                        if aff == 'student':
                            student = True
                if group['id'] == 'fc:fs:fs:prg:ntnu.no:CMED' or group['id'].startswith('fc:fs:fs:kull:ntnu.no:CMED'):
                    for aff in group['membership']['fsroles']:
                        if aff == 'STUDENT':
                            medical_student = True
                # elif group['id'].find('emne:ntnu.no'):
                #     course_code = group['id'].split(':')[-2]
                #     if course_code in ['MD4012', 'MD4020', 'MDT4030', 'MDL4030',
                #                        'MDA4030', 'MD4042', 'MD4043', 'MD4041',
                #                        'MD4044', 'MD4045']:
                #         # Check that within date in group['membership']['notAfter']
                #         if 'notAfter' in group['membership']:
                #             notAfterDate = datetime.strptime(group['membership']['notAfter'], '%Y-%m-%dT%H:%M:%SZ')
                #             print(group['membership']['notAfter'], notAfterDate)
                #             if notAfterDate < datetime.now():
                #                 enrolled_in_relevant_course = True

        if not medical_student and not approved_user:
            raise ProviderException('Only medical students and teachers at NTNU are allowed to login to LearnPathology')

        # The endpoint returns json-data and it needs to be decoded
        extra_data = userinfo_response.json()["user"]

        # Finally test that the audience property matches the client id
        # for validification reasons, as instructed by the Dataporten docs
        # if the userinfo-response is used for authentication
        if userinfo_response.json()["audience"] != app.client_id:
            raise ProviderException(
                "Dataporten returned a user with an audience field \
                 which does not correspond to the client id of the \
                 application."
            )

        return self.get_provider().sociallogin_from_response(
            request,
            extra_data,
        )


class FeideCallbackView(OAuth2View):
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
        client = self.get_client(self.request, app)

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
