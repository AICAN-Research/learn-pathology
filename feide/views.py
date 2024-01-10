from datetime import datetime

from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.base import ProviderException
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)

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

        # Check that user belongs to NTNU
        ntnu_found = False
        for userid_sec in userinfo_response.json()['user']['userid_sec']:
            username = userid_sec.split(':')[1].split('@')[1]
            if username == 'ntnu.no':
                ntnu_found = True
        if not ntnu_found:
            # TODO make this more pretty: Show error message at login page
            raise Exception('Only NTNU users allowed to login!')

        #print(json.dumps(userinfo_response.json(), indent=2))
        userinfo2_response = (
            get_adapter()
                .get_requests_session()
                .get(
                self.extended_user_info,
                headers=headers,
            )
        )
        print(json.dumps(userinfo2_response.json(), indent=2))

        # Get group info
        groupinfo_response = (
            get_adapter()
                .get_requests_session()
                .get(
                self.groups_url,
                headers=headers,
            )
        )

        # Check that user is either: employee at MH faculty or student at given courses
        print(json.dumps(groupinfo_response.json(), indent=2))
        ntnu_found = False
        faculty = False
        student = False
        enrolled_in_relevant_course = False
        for group in groupinfo_response.json():
            if group['id'] == 'fc:org:ntnu.no':
                ntnu_found = True
                if group['membership']['primaryAffiliation'] == 'faculty':
                    # TODO Check that employed at MH faculty or IKOM..
                    faculty = True
                for aff in group['membership']['affiliation']:
                    if aff == 'student':
                        student = True
            elif group['id'].find('emne:ntnu.no'):
                course_code = group['id'].split(':')[-2]
                if course_code in ['MD4012', 'MD4020', 'MDT4030', 'MDL4030',
                                   'MDA4030', 'MD4042', 'MD4043', 'MD4041',
                                   'MD4044', 'MD4045']:
                    # Check that within date in group['membership']['notAfter']
                    if 'notAfter' in group['membership']:
                        notAfterDate = datetime.strptime(group['membership']['notAfter'], '%Y-%m-%dT%H:%M:%SZ')
                        print(group['membership']['notAfter'], notAfterDate)
                        if notAfterDate < datetime.now():
                            enrolled_in_relevant_course = True

        if not ntnu_found:
            raise Exception('Only NTNU users allowed to login!')
        if not faculty:
            if student:
                if not enrolled_in_relevant_course:
                    raise Exception('You are not enrolled to the correct courses to be allowed to login to LearnPathology.')
            else:
                raise Exception('You have to be employed at NTNU or be a medical student to login to LearnPathology.')

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


oauth2_login = OAuth2LoginView.adapter_view(DataportenAdapter)
oauth2_callback = OAuth2CallbackView.adapter_view(DataportenAdapter)
