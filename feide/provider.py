from allauth.socialaccount.providers.base import ProviderAccount, ProviderException
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter
from allauth.socialaccount.adapter import get_adapter

from feide.models import ApprovedUser


class DataportenAdapter(OAuth2Adapter):
    provider_id = 'dataporten'
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
                if group['id'] == 'fc:fs:fs:prg:ntnu.no:CMED' or group['id'].startswith('fc:fs:fs:kull:ntnu.no:CMED') or \
                        group['id'].startswith('fc:fs:fs:emne:ntnu.no:MDI4043'):
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


class DataportenAccount(ProviderAccount):
    def get_avatar_url(self):
        """
        Returns a valid URL to an 128x128 .png photo of the user
        """
        # Documentation for user profile photos can be found here:
        # https://docs.dataporten.no/docs/oauth-authentication/
        base_url = "https://api.dataporten.no/userinfo/v1/user/media/"
        return base_url + self.account.extra_data["profilephoto"]

    def to_str(self):
        """
        Returns string representation of a social account. Includes the name
        of the user.
        """
        dflt = super(DataportenAccount, self).to_str()
        return "%s (%s)" % (
            self.account.extra_data.get("name", ""),
            dflt,
        )


class DataportenProvider(OAuth2Provider):
    id = "dataporten"
    name = "Dataporten"
    account_class = DataportenAccount
    oauth2_adapter_class = DataportenAdapter

    def extract_uid(self, data):
        """
        Returns the primary user identifier, an UUID string
        See: https://docs.dataporten.no/docs/userid/
        """
        return data["userid"]

    def extract_extra_data(self, data):
        """
        Extracts fields from `data` that will be stored in
        `SocialAccount`'s `extra_data` JSONField.

        All the necessary data extraction has already been done in the
        complete_login()-view, so we can just return the data.
        PS: This is default behaviour, so we did not really need to define
            this function, but it is included for documentation purposes.

        Typical return dict:
        {
            "userid": "76a7a061-3c55-430d-8ee0-6f82ec42501f",
            "userid_sec": ["feide:andreas@uninett.no"],
            "name": "Andreas \u00c5kre Solberg",
            "email": "andreas.solberg@uninett.no",
            "profilephoto": "p:a3019954-902f-45a3-b4ee-bca7b48ab507",
        }
        """
        return data

    def extract_common_fields(self, data):
        """
        This function extracts information from the /userinfo endpoint which
        will be consumed by allauth.socialaccount.adapter.populate_user().
        Look there to find which key-value pairs that should be saved in the
        returned dict.

        Typical return dict:
        {
            "userid": "76a7a061-3c55-430d-8ee0-6f82ec42501f",
            "userid_sec": ["feide:andreas@uninett.no"],
            "name": "Andreas \u00c5kre Solberg",
            "email": "andreas.solberg@uninett.no",
            "profilephoto": "p:a3019954-902f-45a3-b4ee-bca7b48ab507",
            "username": "andreas",
        }
        """
        # Make shallow copy to prevent possible mutability issues
        data = dict(data)

        # If a Feide username is available, use it. If not, use the "username"
        # of the email-address
        for userid in data.get("userid_sec"):
            usertype, username = userid.split(":")
            if usertype == "feide":
                data["username"] = username.split("@")[0]
                break
        else:
            # Only entered if break is not executed above
            data["username"] = data.get("email").split("@")[0]

        return data


provider_classes = [DataportenProvider]
